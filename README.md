# Trusted Miner

# Send Deal
https://docs.filecoin.io/store/lotus/very-large-files/#maximizing-storage-per-sector

The default start epoch is the 49 hours after you publish the deal, so it is current_epoch +5880

We recommand you using 4 days for us prepare import for you, so it should be  current_epoch+(24*4+1)*60*2 = current_epoch+11640
md5 is optional.
```
lotus client --start-epoch <current_epoch+11640>  generate-car <inputPath> <outputPath>
```

Please send us the deal CSV with the following format https://github.com/nebulaai/trusted-miner/blob/main/import_deal_template.csv  to us via contact@nbai.io

Note: md5 is optional, but it will good for you when retriving deals


# For miners accept deals

A list of trusted miners by region

NBFS Canada get 5Tb Datacap from Filecoin plus project. As orgnizatin located in North America, NBFS would like to allocate the data to miners in NA and EU.

Please add a pull request to trusted_miner.csv so we can add you to our next sending list.

Thanks.

