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

.default RL_RUN = $80
.default RL_SKIP = $c0

.section code

.public .macro rl_expand destination, source {
    ld hl, source
    ld de, destination
    call rl_expand
}

; Expand runlength encoded data.
; Arguments:
;   de: destination to expand to
;   hl: runlength encoded data
.public rl_expand {
    ld a, (hl)
    inc hl
    cp $80
    jr nc, encoded

    ; literal run
    ld b, a
    ld c, 0
    ldir
    jp rl_expand

encoded:
    cp $c0
    jr nc, skip

    ; fill run
    and $3f
    ld b, a
    ld a, (hl)
    inc hl
:   ld (de), a
    inc de
    djnz :-
    jp rl_expand

skip:
    ; skip
    and $3f
    ret z
    add d
    ld d, a
    jr nc, rl_expand
    inc e
    jp rl_expand
}

.macro set_charset charset {
    ld hl, charset
    ld (current_charset), hl
}

; Set character set for rl_expand_chars.
; Arguments:
;   hl: address of character set
.public set_charset {
    ld (current_charset),hl
    ret
}


; Copy character.
; Arguments:
;   a: number of character
;   hl: destination
; Results:
;   hl: next destination
; Preserves: c, ix, iy
.public copy_character {
    ; calculate character address in de
    ld e,a
    ld d,0
    ccf
    rl e
    rl d
    rl e
    rl d
    rl e 
    rl d
    ld a,(current_charset)
    add a,e
    ld e,a
    ld a,(current_charset + 1)
    adc a,d
    ld d,a

    ; copy character
    ld b, 8
:   ld a,(de)
    ld (hl),a
    inc h
    inc de
    djnz :-

    ; set hl to next destination
    inc l
    jr z, :+
    ld a, h
    sub 8
    ld h, a
:    
}

.public .macro rl_expand_chars destination, source {
    ld hl, destination
    ld iy, source
    call rl_expand_chars
}

; Copy characters of runlength encoded text to screen.
; Arguments:
;   hl: destination to copy to
;   iy: runlength encoded text
.public rl_expand_chars {
    ld a, (iy)
    inc iy
    cp $80
    jr nc, encoded

    ; literal run
    ld c, a
:   ld a, (iy)
    inc iy
    call copy_character
    dec c
    jr nz, :-
    jp rl_expand_chars

encoded:
    cp $c0
    jr nc, skip

    ; fill run
    and $3f
    ld c, a
    ld a, (iy)
    inc iy
:   call copy_character
    dec c
    jr z, rl_expand_chars
    ld a,e
    sub 8
    ld e,a
    ld a,d
    sbc 0
    ld d,a
    jp :-

skip:
    and $3f
    ret z

    ; skip
    add a, l
    ld l, a
    jr nc, rl_expand_chars
    ld a, 8
    add a, h
    ld h, a
    jp rl_expand_chars
}

.section reserved

current_charset .reserve 2
