# Getting started

---

## Creating query account

In this section we will create a query account for your server.

### Creating new identity

It's recommended to create new identity for your bot account. This isn't stricty necessary but separating your ***Main Identity*** from a ***Bot Identity*** allows you to set different **Permissions** and **server**/**channel** groups. Basically this allows the server to treat you and your bot differently

- Launch your TeamSpeak Client and head on to ``Tools -> Identities``
```{image} img/getting_started/teamspeak_identities.png
:alt: Tools -> Identities
:align: center
```

---
- Here we create a new identity for your bot account

```{image} img/getting_started/create_identity.png
:alt: Create identity
```

1. Create a new identity by clicking on ``Create``
2. Modify ``Identity Name`` and ``Nickname`` to match your preference


Now you are ready to connect to a server with your ***Bot Account*** identity

---

### Creating Server Query login

---


```{warning}
Don't make your login name too complicated. You should't have **spaces** or **special characters** in your login name
```

---

### Permissions

#### To Login
- ``b_client_create_modify_serverquery_login``
- ``b_serverquery_login``


#### Essentials
- ``b_virtualserver_select``
- ``b_virtualserver_notify_register``

#### Recommended
- ``b_client_server_textmessage_send``


## Example bot
```{literalinclude} ../examples/simple_example.py
```