;  rl-expand.s -- expand run length encoded data.
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

rl_tmp .reserve 1

.section code

; source_ptr: runlength encoded string
; destination_ptr: destination to expand to

.public .macro rl_expand destination, source {
    store_word destination_ptr, destination
    store_word source_ptr, source
    jsr rl_expand
}

.public rl_expand {
    ldy #0
loop:
    lda (source_ptr),y
    bmi encoded

    ; literal run
    inc_16 source_ptr
    tay
    tax
    dey
:   lda (source_ptr),y
    sta (destination_ptr),y
    dey
    bpl :-
    iny
    clc
    txa
    adc source_ptr
    sta source_ptr
    bcc :+
    inc source_ptr + 1
    clc
:   txa
    adc destination_ptr
    sta destination_ptr
    bcc loop
    inc destination_ptr + 1
    bne loop

encoded:
    cmp #$c0
    bcs skip

    ; fill run
    and #$3f
    sta rl_tmp
    iny
    lda (source_ptr),y
    ldy rl_tmp
    dey
:   sta (destination_ptr),y
    dey
    bpl :-
    iny
    clc
    lda #2
    adc source_ptr
    sta source_ptr
    bcc :+
    inc source_ptr + 1
    clc
:   lda rl_tmp
    adc destination_ptr
    sta destination_ptr
    bcc loop
    inc destination_ptr + 1
    bne loop

skip:
    ; skip
    inc_16 source_ptr
    and #$3f
    beq end
    clc
    adc destination_ptr
    sta destination_ptr
    bcc loop
    inc destination_ptr + 1
    bne loop

end:
    rts
}
