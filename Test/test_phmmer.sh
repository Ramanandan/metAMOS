../initPipeline -l flx -f -m carsonella_pe_filt.fna -d test_phmmer -i 3000:4000 
../runPipeline -r -v -c phmmer -p 8 -a soap -d test_phmmer -k 55 -f Preprocess,Assemble,Annotate,Postprocess -z phylum
