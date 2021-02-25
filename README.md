# Swan Client
Swan Client is a pragmatical tool to help client and miner automated the offline deal sending and importing process.

In Swan project, a client is defined as a user who want to send out a deal, and a miner is a Filecoin node who want to import and sealing the deal to Filecoin network.


## Using the Swan API

The Swan API can be used to programmatically retrieve and analyze data, as well as engage with the conversation on
Twitter.

This API provides access to a variety of different resources including the following:

* Authorization
* Miners
* Tasks

## How to get access to the Swan API

### Step one: Signup a swan account

You can create an account on [Filswan](https://www.filswan.com) site, afte login you, can create

### Step two: Save your App's key and tokens and keep them secure

Within your "My Profile" ->"Tools" ,You have the chance to generate a set of Access Tokens that can be used to make
requests on behalf of your personal Twitter account, and a Bearer Token that can be used to authenticate endpoints that
require jwt Bearer Token. Since these keys and tokens do not expire unless regenerated, we suggest creating
environment variables or using a secure password manager.

### Step three: Set up your access
You can get your jwt Bearer Token via the following API.
```
curl --location --request POST 'https://api.filswan.com/user/api_keys/jwt' \
--data-raw '{
    "access_token": "my-access-token",
    "apikey": "my-apikey"
}'
```

Once you get the token, you can use it to access Swan APIs via postman or other API tools.
## Supported API Document

Please check bellow for the APIs currently supported

[Filswan APIs](https://documenter.getpostman.com/view/13140808/TWDZJbzV)

## Client Tool

Client Tool provide the following functions:

* Generate Car file from downloaded files.
* Create CSV file for miner pre-download the car file with the url you defined.
* Propose deal from the local car file
* Create CSV file contains deal ID and miner id for miner processing.

## How to use client tool

Please check the [Client Tool Guide](https://github.com/nebulaai/swan/tree/main/client)

# Miner tool

* Miner car file downloader
* Miner importer
* Deal status updater

## How to use the miner tool

Please check the [Miner Tool Guide](https://github.com/nebulaai/swan/tree/main/miner)
