---
title: "DFlare: Scaling Up Draft Capacity for Block Diffusion Speculative Decoding"
arxiv_id: "2606.02091"
published: "2026-06"
authors: "Jiebin Zhang, Zhenghan Yu, Song Liu, Eugene J. Yu, Zheng Li, Dawei Zhu, Jiangshan Duo, Weimin Xiong, Yifan Song, Guanghua Yu, Jianchen Zhu, Sujian Li"
tags:
  - speculative-decoding
  - block-diffusion
  - draft-capacity
  - diffusion-lm
  - inference-acceleration
abstract: "Block diffusion speculative decoding accelerates generation by using a diffusion-based draft model that generates blocks of tokens in parallel. However, the draft capacity — the number of tokens a draft model can generate per step — has been a limiting factor. DFlare introduces techniques to scale up draft capacity for block diffusion speculative decoding. By employing progressive masking schedules and hierarchical draft architectures, DFlare enables draft models to generate longer and more accurate token blocks. The framework achieves 3-4x speedup on text generation benchmarks, with the draft capacity scaling from 4 tokens per step to 16+ tokens, significantly reducing the number of verification passes needed."
---

# DFlare: Scaling Up Draft Capacity for Block Diffusion Speculative Decoding

**arXiv ID:** 2606.02091  
**Published:** 2026-06  
**Authors:** Jiebin Zhang, Zhenghan Yu, Song Liu, et al.  
**URL:** https://arxiv.org/abs/2606.02091

## Abstract

Block diffusion speculative decoding accelerates generation by using a diffusion-based draft model that generates blocks of tokens in parallel. However, the draft capacity — the number of tokens a draft model can generate per step — has been a limiting factor. DFlare introduces techniques to scale up draft capacity for block diffusion speculative decoding. By employing progressive masking schedules and hierarchical draft architectures, DFlare enables draft models to generate longer and more accurate token blocks. The framework achieves 3-4x speedup on text generation benchmarks, with the draft capacity scaling from 4 tokens per step to 16+ tokens, significantly reducing the number of verification passes needed.
