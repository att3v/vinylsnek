TODO:

 - replace cover art fetching to coverartarchive if possible 
 - add fields for purchase date and price in add record -dialog 
 - add a summary dialog 
 - implement editing and filtering 
 - searching could be useful too 
 - parse descriptions for color words so that filtering can be made against them 
 - use webcam as barcode reader? 
 - import from discogs exports 
 - Add records by discogs release ID in case there are no barcodes available 
 - It seems like the data can be crap for the release IDs in the barcode search
    - example: barcode 634164422882 (The Callous Daoboys) returns a match for release ID 3849204, which is claimed to be the same record in the search results, but clearly isn't. (Gamardah Fungus)
 
 
DID DO:
 - probably no need for discogs_client 
 - find a way to resolve specific release in the case of overlapping barcodes 
