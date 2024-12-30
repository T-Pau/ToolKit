;  rl-expand-bitmap.s -- expand run length encoded data.
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

.section zero_page

rl_high .reserve 1

.section reserved

.public rl_charset .reserve 1


.section code

.public .macro rl_expand_bitmap destination, source {
    store_word destination_ptr, destination
    store_word source_ptr, source
    jsr rl_expand_bitmap
}

; rl_expand_bitmap -- expand runlength encoded string, rendering it into bitmap
; Arguments:
;   source_ptr: runlength encoded string
;   destination_ptr: destination to expand to
;   rl_charset: high byte of charset
.public rl_expand_bitmap {
    ldy #0
loop:
    lda (source_ptr),y
    bmi encoded

    ; literal run
    inc_16 source_ptr
    tax
copy_literal:
    lda (source_ptr),y
    inc_16 source_ptr

; XLR8:    rl_expand_bitmap_decode_char load_literal + 1
    asl
    rol rl_high
    asl
    rol rl_high
    asl
    rol rl_high
    sta load_literal + 1
    lda rl_high
    and #$07
    ora rl_charset
    sta load_literal + 1 + 1

    ldy #7
load_literal:
    lda $1000,y
    sta (destination_ptr),y
    dey
    bpl load_literal
    add_word destination_ptr, 8
    iny
    dex
    bne copy_literal
    beq loop

encoded:
    cmp #$c0
    bcs skip

    ; fill run
    and #$3f
    tax
    inc_16 source_ptr
    lda (source_ptr),y
    inc_16 source_ptr
; XLR8:    rl_expand_bitmap_decode_char load_run + 1
    asl
    rol rl_high
    asl
    rol rl_high
    asl
    rol rl_high
    sta load_run + 1
    lda rl_high
    and #$07
    ora rl_charset
    sta load_run + 1 + 1

run_loop:
    ldy #7
load_run:
    lda $1000,y
    sta (destination_ptr),y
    dey
    bpl load_run
    add_word destination_ptr, 8
    dex
    bne run_loop
    iny
    jmp loop

skip:
    inc_16 source_ptr
    and #$3f
    beq end

    asl
    asl
    asl
    bcc :+
    inc destination_ptr + 1
    clc
:   adc destination_ptr
    sta destination_ptr
    bcc :+
    inc destination_ptr + 1
:   jmp loop

end:
    rts
}


; rl_expand_bitmap_decode_char -- prepare load for character data
; Arguments:
;   A: character
;   target: where to store character data address
; Preserves: X Y
.macro rl_expand_bitmap_decode_char target {
    asl
    rol rl_high
    asl
    rol rl_high
    asl
    rol rl_high
    sta target
    lda rl_high
    and #$07
    ora rl_charset
    sta target + 1
}
