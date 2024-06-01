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

RL_RUN = $ff
RL_SKIP = $fe

.section code

.public .macro rl_encode length, byte {
    .if length > 255 {
        .repeat i, length / 255 {
            .data RL_RUN, 255, byte
        }
    }
    ;.data $ff, length .mod 255, byte
    .data RL_RUN, length - 255 * (length / 255):1, byte
}

.public .macro rl_skip length {
    .if length > 255 {
        .repeat i, length / 255 {
            .data RL_SKIP, $ff
        }
    }
    ;.data $ff, length .mod 255, byte
    .data RL_SKIP, length - 255 * (length / 255):1
}

.public .macro rl_end {
    .data RL_RUN, $00
}

; soucre_ptr: runlength encoded string
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
    inc_16 source_ptr
    cmp #RL_SKIP
    bne no_skip
    lda (source_ptr),y
    inc_16 source_ptr
    clc
    adc destination_ptr
    sta destination_ptr
    bcc loop
    inc destination_ptr + 1
    bne loop
no_skip:
    ldx #$01
    cmp #RL_RUN
    bne runlength_loop
    lda (source_ptr),y
    inc_16 source_ptr
    cmp #$00
    bne :+
    rts
:   tax
    lda (source_ptr),y
    inc_16 source_ptr
runlength_loop:
    sta (destination_ptr),y
    iny
    dex
    bne runlength_loop
    tya
    clc
    adc destination_ptr
    sta destination_ptr
    bcc :+
    inc destination_ptr + 1
:   jmp rl_expand
}
