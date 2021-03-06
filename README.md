# Swan Tool Kits

Swan Tool Kits is a set of pragmatical tools to help client and miner automated the offline deal sending and importing
process.

In Swan project, a client is defined as a user who sends out deals, and a miner is a Filecoin node who imports and seals
the deals to Filecoin network. A general guide of lotus offline deal can be found here:

https://docs.filecoin.io/store/lotus/very-large-files


## If you are a client who wants to send deals


Client Tool provides the following functions:

* Generate Car files from downloaded source files.
* Generate metadata e.g. Car file URI, start epoch, etc. and save them to a metadata CSV file.
* Propose deals based on the metadata CSV file.
* Generate a final CSV file contains deal IDs and miner id for miner to import deals.
* Create tasks on Swan Platform.

### How to use the client tool

```shell
git clone https://github.com/nebulaai/swan
cd swan/miner
```
Please check the [Client Tool Guide](https://github.com/nebulaai/swan/tree/main/client)

## If you are a miner who wants to import deals
Miner Tool provides the following functions:
* Download Car file.
* Import Car file.
* Update deal status on Swan Platform.

### How to use the miner tool

```shell
git clone https://github.com/nebulaai/swan
cd swan/miner
```
Please check the [Miner Tool Guide](https://github.com/nebulaai/swan/tree/main/miner)

## If you are a developer who wants to use Swan APIs

The Swan APIs can be used to programmatically retrieve and analyze data.

These APIs provide access to a variety of different resources including the following:

* Authorization
* Miners
* Tasks

### How to get access to the Swan APIs

#### Step one: Signup a swan account

You can create an account on [Filswan](https://www.filswan.com) site to get the API key support.

#### Step two: Save your API keys and tokens and keep them secure

Under "My Profile"->"Developer Settings", you can generate a set of API Keys and Access Tokens which can be used
to make requests on behalf of your personal Swan account. Since these API keys and Access Tokens do not expire unless regenerated, we suggest
creating environment variables or using a secure password manager.

#### Step three: Set up your access

You can get your jwt Bearer Token via the following API.

```shell
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
