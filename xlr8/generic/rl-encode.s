;  rl-encode.s -- run length encode data
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

.public .macro rl_encode length, byte {
    .if length > 63 {
        .repeat i, length / 63 {
            .data RL_RUN + 63, byte:1
        }
    }
    ;.data RL_RUN + length .mod 63, byte:1
    .data RL_RUN + length - 63 * (length / 63):1, byte:1
}

.public .macro rl_skip length {
    .if length > 63 {
        .repeat i, length / 63 {
            .data RL_SKIP + 63
        }
    }
    ;.data RL_SKIP + length .mod 63
    .data RL_SKIP + length - 63 * (length / 63):1
}

.public .macro rl_literal b0, b1 = .none, b2 = .none, b3 = .none {
    .if b3 == .none {
        .if b2 == .none {
            .if b1 == .none {
                .data $01, b0:1
            }
            .else {
                .data $02, b0:1, b1:1
            }
        }
        .else {
            .data $03, b0:1, b1:1, b2:1
        }
    }
    .else {
        .data $04, b0:1, b1:1, b2:1
    }
}

.public .macro rl_end {
    .data RL_SKIP
}
