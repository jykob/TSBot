# Getting started

In this chapter we are going to get you started with TSBot.

---

## Creating a new TeamSpeak identity

It's recommended to create a new identity for your bot account. This isn't strictly necessary but separating your **_Main Identity_** from a **_Bot Identity_** allows you to set different **Permissions** and **server**/**channel** groups. Basically this allows the server to treat you and your bot differently.

Launch your TeamSpeak Client and head on to:  
`Tools → Identities`

```{image} ../img/getting_started/teamspeak_identities.png
:alt: "Open Identities window: Tools → Identities"
:align: center
:class: margin-bottom
```

Here we create a new identity for your bot account

```{image} ../img/getting_started/create_identity.png
:alt: Create identity
```

1. Create a new identity by clicking on `Create`.
2. Modify `Identity Name` and `Nickname` to match your preference.

Now you are ready to connect to a server with your **_Bot Account_** identity.

---

## Connecting with specific identity

Now that we have an identity for your **_Bot Account_**, You can use it to connect to your server:  
`Connections → Connect`

```{image} ../img/getting_started/teamspeak_connect.png
:alt: Connections → Connect
```

To change your connection identity:

```{image} ../img/getting_started/change_identity.png
:alt: Change connection identity
```

1. Click `▼ More` on the bottom left.
2. Select the right identity from the `Identity` dropdown
3. Connect

---

## Setting up permissions

In order to get your bot to work, you need to give it some permissions.

Recommended ways to give these permissions are:

1. With **Server Groups**:
   - Give a server group the permissions needed and give the bot client a such server group.
2. With **Client Permissions**:
   - This will give the permissions to a specific client UID.

### Essential

```{table}
:width: 100%

| Permission name                              | Reason                                           |
| -------------------------------------------- | ------------------------------------------------ |
| ``b_client_create_modify_serverquery_login`` | To create/modify ***ServerQuery*** accounts      |
| ``b_virtualserver_notify_register``          | To register the server to send events to the bot |
```

### Recommended

```{table}
:width: 100%

| Permission name                        | Reason                                                                                                        |
| -------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| ``b_client_server_textmessage_send``   | To send messages in Server chat                                                                               |
| ``b_client_channel_textmessage_send``  | To send messages in Channel chat                                                                              |
| ``i_client_private_textmessage_power`` | To send messages in Private chat.<br />Should match the highest<br />``i_client_needed_private_textmessage_power`` |
```

---

## Creating ServerQuery login

Now that we are connected, we are ready create the login for your **_ServerQuery_** account.  
`Tools → ServerQuery Login`

```{image} ../img/getting_started/serverquery_login.png
:alt: "Create ServerQuery login: Tools → ServerQuery Login"
:align: center
```

```{note}
If you can't click on the ``ServerQuery Login``, you don't have the proper permissions on your client.
Check [](#setting-up-permissions) for more information.
```

This will prompt you for a **_ServerQuery_** login. Enter a suitable login name for your bot.

```{image} ../img/getting_started/login_prompt.png
:alt: Enter your ServerQuery login name
:align: center
:class: margin-bottom
```

```{warning}
Don't make your login name too complicated. You should't have **spaces** or **special characters** in your login name.
This can cause you to be unable to login.
```

After clicking `OK`, you will be prompted with _Your ServerQuery Login_.  
Take a note of the `Name` and `Password`, these are your `username` and `password` when logging in.

```{image} ../img/getting_started/login_password.png
:alt: Generated ServerQuery login
:align: center
:class: margin-bottom
```

```{note}
If you lose your login info or want to change login name, just repeat the steps in this section.
This will generate you a new login.
```

---

## Show connected query clients

By default, TeamSpeak doesn't show connected query clients.  
To enable this feature you need to add the server to your **_Bookmarks_** and editing the bookmark.

```{image} ../img/getting_started/bookmarks.png
:alt: Toggle 'Show ServerQuery Clients'
:align: center
:class: margin-bottom
```

After reconnect to the server using the bookmark and you'll see the connected ServerQuery clients.

```{image} ../img/getting_started/example_clients.png
:alt: Example of a shown ServerQuery client
:align: center
:class: margin-bottom
```

````{note}
If you still don't see the ServerQuery client, check permissions.


```{table}
:align: center

| Your permissions                    |   Is   |             ServerQuery client permissions |
| :---------------------------------- | :----: | -----------------------------------------: |
| ``i_client_serverquery_view_power`` | **>=** | ``i_client_needed_serverquery_view_power`` |
```

````

---

## Creating ServerQuery bot with TSBot

To create our first TSBot, we can use the [examples/simple_example.py](https://github.com/0x4aK/TSBot/blob/master/examples/simple_example.py)

Let's copy the example and modify the script to fit our needs:

9. Replace `USERNAME` with your ServerQuery Name.
10. Replace `PASSWORD` with your ServerQuery Password.
11. Replace `ADDRESS` with your TeamSpeak server address.

```{literalinclude} ../../examples/simple_example.py
:linenos: true
:emphasize-lines: 8, 9, 10
```

Now run the script. A **_ServerQuery client_** should join to your server.

```{image} ../img/getting_started/example_clients.png
:alt: Example of a shown ServerQuery client
:align: center
:class: margin-bottom
```

---

<div class="flex flex-row">

As long as the script is running, every time someone joins the server, they will get poked with this:

```{image} ../img/getting_started/example_event.png
:alt: Example of client joining getting poked
:class: max-width-50 height-max-content
```

</div>

---

<div class="flex flex-row">

And you can use command `!hello` to say hello to the bot

```{image} ../img/getting_started/example_command.png
:alt: Example of using command !hello
:class: max-width-50 height-max-content
```

</div>
