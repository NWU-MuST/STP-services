#!/bin/bash
. ./cmd.sh

steps/make_denlats.sh --nj 10 --sub-split 20 --cmd "$train_cmd" \
  --transform-dir exp/tri3b_ali \
  data/train data/lang exp/tri4a exp/tri4a_denlats || exit 1;

steps/train_mmi.sh --cmd "$train_cmd" --boost 0.1 \
  data/train data/lang exp/tri3b_ali exp/tri4a_denlats \
  exp/tri4a_mmi_b0.1  || exit 1;

steps/decode.sh --nj 10 --cmd "$decode_cmd" --transform-dir exp/tri3b/decode \
  exp/tri3b/graphs data/test exp/tri4a_mmi_b0.1/decode

#first, train UBM for fMMI experiments.
steps/train_diag_ubm.sh --silence-weight 0.5 --nj 20 --cmd "$train_cmd" \
  600 data/train data/lang exp/tri3b_ali exp/dubm4a

# Next, fMMI+MMI.
steps/train_mmi_fmmi.sh \
  --boost 0.1 --cmd "$train_cmd" data/train data/lang exp/tri3b_ali exp/dubm4a exp/tri4a_denlats \
  exp/tri4a_fmmi_a || exit 1;

for iter in 3 4 5 6 7 8; do
 steps/decode_fmmi.sh --nj 10  --cmd "$decode_cmd" --iter $iter \
   --transform-dir exp/tri3b/decode  exp/tri3b/graphs data/test \
  exp/tri4a_fmmi_a/decode_it$iter
done

# decode the last iter with the bd model.
for iter in 8; do
 steps/decode_fmmi.sh --nj 10  --cmd "$decode_cmd" --iter $iter \
   --transform-dir exp/tri3b/decode  exp/tri3b/graphs data/test \
  exp/tri4a_fmmi_a/decode_it$iter
done

# fMMI + mmi with indirect differential.
steps/train_mmi_fmmi_indirect.sh \
  --boost 0.1 --cmd "$train_cmd" data/train data/lang exp/tri3b_ali exp/dubm4a exp/tri4a_denlats \
  exp/tri4a_fmmi_indirect || exit 1;

for iter in 3 4 5 6 7 8; do
 steps/decode_fmmi.sh --nj 10  --cmd "$decode_cmd" --iter $iter \
   --transform-dir exp/tri3b/decode  exp/tri3b/graphs data/test \
  exp/tri4a_fmmi_indirect/decode_it$iter
done

