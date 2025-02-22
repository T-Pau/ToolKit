;  irq.s -- Handle multiple raster IRQs.
;  Copyright (C) Dieter Baron
;
;  This file is part of Toolkit.
;  The authors can be contacted at <toolkit@tpau.group>.
;
;  Redistribution and use in source and binary forms, with or without
;  modification, are permitted provided that the following conditions
;  are met:
;  1. Redistributions of source code must retain the above copyright
;     notice, this list of conditions and the following disclaimer.
;  2. The names of the authors may not be used to endorse or promote
;     products derived from this software without specific prior
;     written permission.
;
;  THIS SOFTWARE IS PROVIDED BY THE AUTHORS "AS IS" AND ANY EXPRESS
;  OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
;  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
;  ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY
;  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
;  DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
;  GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
;  INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER
;  IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
;  OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN
;  IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

; .define IRQ_DEBUG

.pre_if .defined(C64)
END_OF_IRQ = $ea81
.define USE_VICII

.pre_else_if .defined(C128)
END_OF_IRQ = $ff33
.define USE_VICII

.pre_else_if .defined(MEGA65)
.section code
END_OF_IRQ {
    pla
    tay
    pla
    tax
    pla
    rti
}
.define USE_VICII

.pre_else_if .defined(PLUS4) || .defined(C16)
END_OF_IRQ = $fcbe
.define USE_TED

.pre_else_if .defined(VIC20)
VIC_VERTICAL_ORIGIN = VIC_CONTROL_1

END_OF_IRQ = $eb18
.define USE_VIC

.pre_else
; .error "Target not supported"
.pre_end

.pre_if .defined(USE_VICII)
BORDERCOLOR = VIC_BORDER_COLOR
HLINE_LOW = VIC_RASTER
HLINE_HIGH = VIC_CONTROL_1
HLINE_BIT8 = $80
IRR = VIC_INTERRUPT_REQUEST
IMR = VIC_INTERRUPT_MASK
IRQ_RASTER = 1

.pre_else_if .defined(USE_VIC)

BORDERCOLOR = VIC_COLOR

.pre_else_if .defined(USE_TED)
BORDERCOLOR = TED_BORDER_COLOR
HLINE_LOW = $FF0B
HLINE_HIGH = $FF0A
HLINE_BIT8 = 1
IRR = $FF09
IMR = $FF0A
IRQ_RASTER = 2
.pre_end

.section zero_page

table .reserve 2

.section reserved

irq_index .reserve 1

table_length .reserve 1

.pre_if .defined(USE_VIC)
next_line .reserve 1

timer_length .reserve 2

.public is_ntsc .reserve 1

lines_per_frame .reserve 1
.pre_end

.section code

.macro set_irq_table new_table {
    load_word new_table
    lda #.sizeof(new_table)
    jsr set_irq_table
}

.public init_irq {
    php
    sei
    .if .defined(USE_VICII) {
        ; disable cia 1 interrupts
        lda #$7f
        sta CIA1_INTERRUPT
        ; enable rasterline irq
        lda #1
        sta VIC_INTERRUPT_MASK
    }
    .else_if .defined(USE_VIC) {
        ; set up constants for PAL/NTSC
        ldx #0
        ldy #312/2
        lda VIC_VERTICAL_ORIGIN
        cmp #$19
        bne :+
        inx
        ldy #261/2
    :   stx is_ntsc
        sty lines_per_frame

        lda #$7f
        sta VIA1_INTERRUPT_MASK    ; disable all interrupts on VIA1
        sta VIA2_INTERRUPT_MASK    ; disable all interrupts on VIA2
        ; set timer 1 to free run
        lda	#$40
        sta	VIA2_CONTROL_1
        ; enable timer 1 interrupts
        lda #$c0
        sta VIA2_INTERRUPT_MASK
        ; set initial run time to more than 1 frame
        lda #$00
        sta VIA2_TIMER_1_LOAD
        lda #87
        sta VIA2_TIMER_1_LOAD + 1
    }
    .else_if .defined(USE_TED) {
        ; enable rasterline irq
        ldx #IRQ_RASTER
        stx IMR
    }

    lda IRQ_VECTOR
    sta kernal_irq
    lda IRQ_VECTOR + 1
    sta kernal_irq + 1
    lda #<irq_main
    sta IRQ_VECTOR
    lda #>irq_main
    sta IRQ_VECTOR + 1
    plp
    rts
}


; Restores Kernal IRQ routine.
.public restore_irq {
    php
    sei
    lda IRQ_VECTOR
    cmp #<irq_main
    bne end
    lda IRQ_VECTOR + 1
    cmp #>irq_main
    bne end
    .if .defined(USE_VICII) {
        ; enable cia 1 interrupts
        lda #$81
        sta CIA1_INTERRUPT
        ; disable rasterline irq
        lda #0
        sta VIC_INTERRUPT_MASK
    }

    lda kernal_irq
    sta IRQ_VECTOR
    lda kernal_irq + 1
    sta IRQ_VECTOR + 1
end:    
    plp
    rts
}

.public set_irq_table {
    php
    sei
    stx table
    sty table + 1
    sta table_length
    lda #0
    sta irq_index
    jsr setup_next_irq
    plp
    rts
}


irq_main {
    .if .defined(USE_VIC) {
        ;dec BORDERCOLOR
        ; synchronize with raster line
        lda next_line
    :   cmp VIC_RASTER
        bne :-
        ;inc BORDERCOLOR
    }
    .if .defined(IRQ_DEBUG) {
        inc BORDERCOLOR
    }
    .if .defined(C128) {
        lda #$0e
        sta MMU_CONFIGURATION
    }
.private irq_jsr:
    jsr $0000
    jsr setup_next_irq
    ; acknowledge irq
    .if .defined(USE_VIC) {
        lda VIA2_TIMER_1
    }
    .else {
        lda #IRQ_RASTER
        sta IRR
    }
    .if .defined(IRQ_DEBUG) {
        dec BORDERCOLOR
    }
    jmp END_OF_IRQ
}


setup_next_irq {
    ldy irq_index

    .if .defined(USE_VIC) {
        lda #0
        sta timer_length + 1
        lda (table),y
        sta next_line
        sec
        sbc VIC_RASTER
        bcs :+
        adc lines_per_frame
    :	sbc #2
        sta timer_length
        asl
        rol timer_length + 1    ; 10
        asl
        rol timer_length + 1    ; 100
        asl
        rol timer_length + 1    ; 1000
        asl
        rol timer_length + 1    ; 10000
        ldx is_ntsc
        bne :+
        adc timer_length
        bcc :+
        inc timer_length + 1
    :	asl
        rol timer_length + 1    ; 1000x0
        ldx is_ntsc
        bne :+
        adc timer_length
        bcc :+
        inc timer_length + 1
    :	asl
        rol timer_length + 1    ; 1x000xx
        adc timer_length
        bcc :+
        inc timer_length + 1
    :	asl
        rol timer_length + 1    ; 1x000xx10
        sta VIA2_TIMER_1
        lda timer_length + 1
        sta VIA2_TIMER_1 + 1
    }
    .else {
        ; activate next entry
        lda (table),y
        sta HLINE_LOW
        iny
        lda (table),y
        beq high0
        lda HLINE_HIGH
        ora #HLINE_BIT8
        sta HLINE_LOW
        bne addr
    high0:
        lda HLINE_HIGH
        and #HLINE_BIT8 ^ $ff
        sta HLINE_HIGH
    }
addr:
    iny
    lda (table),y
    sta irq_jsr + 1
    iny
    lda (table),y
    sta irq_jsr + 2

    iny
    cpy table_length
    bne :+
    ldy #0
:	sty irq_index
    rts
}

.section reserved

kernal_irq .reserve 2