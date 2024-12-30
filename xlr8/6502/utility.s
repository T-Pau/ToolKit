;  utility.s -- utility macros
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

.public .macro adc_16 address {
    adc address
    sta address
    bcc :+
    inc address + 1
:
}


.public .macro inc_16 address {
    inc address
    bne :+
    inc address + 1
:
}

; Load address into X/Y
.public .macro load_word address {
    ldx #<address
    ldy #>address
}

.public .macro store_word address, value {
    lda #<(value)
    sta address
    lda #>(value)
    sta address + 1
}

.public .macro store_word_indexed address, table {
    lda table,x
    sta address
    lda table + 1,x
    sta address + 1
}

.public .macro add_word address, value {
    clc
    lda address
    adc #<(value)
    sta address
    .if value < 256 {
        bcc :+
        inc address + 1
      :
    }
    .else {
        lda address + 1
        adc #>(value)
        sta address + 1
    }
}


.public .macro subtract_word address, value {
    sec
    lda address
    sbc #<(value)
    sta address
    .if value < 256 {
        bcs :+
        dec address + 1
          :
    }
    .else {
        lda address + 1
        sbc #>(value)
        sta address + 1
    }
}
