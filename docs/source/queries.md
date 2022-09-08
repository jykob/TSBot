---
myst:
  substitutions:
    TSQuery: "[TSQuery](tsbot.query_builder.TSQuery)"
    query: "[query](tsbot.query_builder.query)"
---

# Queries

{{env.config.project}} implements a query builder to ease the use of building commands.  
In this chapter you will learn how to use the query system in {{env.config.project}}

---

## Creating query objects

Creating a query object is as easy as calling a function.  
This can be achieved by importing {{query}} from `tsbot` and calling it with the desired command.

```
from tsbot import query

clientlist_query = query("clientlist")
```

This creates {{TSQuery}} object which you can manipulate to build out your command.

---

## Manipulating TSQuery objects

In this section, we will learn how you can create your command using queries.

All the methods provided (exc. [compile()](<tsbot.query_builder.TSQuery.compile()>)) by the {{TSQuery}} returns an instance of themselves.
This allows you to [method cascade](https://en.wikipedia.org/wiki/Method_cascading) your calls to the object.

### Adding options

You can add options to your commands by using [option()](<tsbot.query_builder.TSQuery.option()>) method.  
The method [option()](<tsbot.query_builder.TSQuery.option()>) accepts as **_many arguments_** as you provide it or you can add them **_one by one_**.

```
from tsbot import query

example_query = query("clientlist")

example_query.option("groups", "uid", "away")

# ---- OR ----

example_query.option("groups")
example_query.option("uid")
example_query.option("away")
```

### Adding parameters

Adding parameters to your command by using [params()](<tsbot.query_builder.TSQuery.params()>) method.  
The method [params()](<tsbot.query_builder.TSQuery.params()>) accepts parameters as a **_key-value_** pair. You can supply as **_many arguments_** as want or add them **_one by one_**.

Values can be anything that implements `__str__()` method. The method [params()](<tsbot.query_builder.TSQuery.params()>) calls [str()](str) on each value that is added.  
Mainly these will be: [str](str) | [int](int) | [float](float) | [bytes](bytes)

Since [params()](<tsbot.query_builder.TSQuery.params()>) accepts **_keys_** and **_values_**, this allows us to build the parameters as a [dict](dict) and spread the dictionary when calling the method.

```
from tsbot import query

example_query = query("clientpoke")

example_query.params(clid=1, msg="Wake up!")

# ---- OR ----

example_query.params(clid=1)
example_query.params(msg="Wake up!")

# ---- OR ----

params = {"clid": 1, "msg": "Wake up!"}
example_query.params(**params)
```

### Adding parameter blocks

Adding parameter blocks to your command by using [param_block()](<tsbot.query_builder.TSQuery.param_block()>) method.  
This works much like [params()](<tsbot.query_builder.TSQuery.params()>), but you can add multiple **_values_** to a given **_key_**.

This can be handy when a command allows you to specify multiple targets.
For example command `clientmove` allows you to specify multiple `clid`'s to move.

```
from tsbot import query

example_query = query("clientmove")
example_query.params(cid=1)        # Set the channel where to move clients
example_query.param_block(clid=2)  # Selecting client_id #2 to be moved
example_query.param_block(clid=3)  # Selecting client_id #3 to be moved
example_query.param_block(clid=6)  # Selecting client_id #6 to be moved
```

````{warning}
Each parameter block has to be a new call to [param_block()](<tsbot.query_builder.TSQuery.param_block()>).
For example you **cannot** do this:
```
example_query.param_block(clid=2, clid=3, clid=6)
```
````

### Method cascading

Method cascading allows you to make multiple method calls to a `TSQuery` object.  
You can mix and match the order of these calls, this will still compile to a suitable result.

```
from tsbot import query

example_query = (
    query("clientmove")
    .param_block(clid=2)
    .option("continueonerror")
    .params(cid=4)
    .param_block(clid=3)
    .params(cpw="s3cr3t p4ssw0rd")
)
```

### Compiling commands

If you want to see the raw command produced by the `TSQuery` object, you can [compile()](<tsbot.query_builder.TSQuery.compile()>) it.
This returns the raw command that will be sent to the server.

```
from tsbot import query

example_query = query("clientlist").option("groups")

raw_command = example_query.compile()
```

Once `TSQuery` object has been compiled, it will cache the results.
If `TSQuery` is compiled again without modifications, it will return the cached results.
This means that you don't have to cache the commands yourself for example in a variable.
You can just send the query again and again via [send()](<tsbot.bot.TSBot.send()>)

---

## Examples

Now that we know how to use {{TSQuery}} objects, let's see some real life examples how to use them.

All of these examples are from **TeamSpeak _ServerQuery_ manual**.

---

Goal:
`clientlist -uid -away -groups`

```
from tsbot import query

clientlist_query = query("clientlist").option("uid", "away", "groups")

print(clientlist_query.compile()) # clientlist -uid -away -groups
```

---

Goal:
`clientdbfind pattern=FPMPSC6MXqXq751dX7BKV0JniSo= -uid`

In this example we can see that you could add parameters to the {{TSQuery}} object **_line by line_** or all in **_one assignment_**

```
from tsbot import query

clientdbfind_query = query("clientdbfind")
clientdbfind_query.params(pattern="FPMPSC6MXqXq751dX7BKV0JniSo")
clientdbfind_query.option("uid")

# ---- OR ----

clientdbfind_query = (
    query("clientdbfind")
    .params(pattern="FPMPSC6MXqXq751dX7BKV0JniSo")
    .option("uid")
)

print(clientdbfind_query.compile()) # clientdbfind pattern=FPMPSC6MXqXq751dX7BKV0JniSo -uid
```

---

Goal:
`clientkick reasonid=5 reasonmsg=Go\saway! clid=1|clid=2|clid=3`

In this example adding parameter blocks to queries can be achieved multiple ways.
Either using normal **_for loops_** or one-liner **_list comprehension_**.

```
from tsbot import query

clientkick_query = query("clientkick").params(reasonid=5, reasonmsg="Go away!")
for client_id in (1, 2, 3):
    clientkick_query.param_block(clid=client_id)

# ---- OR ----

clientkick_query = query("clientkick").params(reasonid=5, reasonmsg="Go away!")
[clientkick_query.param_block(clid=client_id) for client_id in (1, 2, 3)]

print(clientkick_query.compile()) # clientkick reasonid=5 reasonmsg=Go\saway! clid=1|clid=2|clid=3
```

---

Goal:
`clientaddperm cldbid=16 permid=17276 permvalue=50 permskip=1|permid=21415 permvalue=20 permskip=0`

In this example we can see that parameter blocks can have multiple parameters attacted to it.

```
from tsbot import query

clientaddperm_query = query("clientaddperm").params(cldbid=16)
clientaddperm_query.param_block(permid=17276, permvalue=50, permskip=1)
clientaddperm_query.param_block(permid=21415, permvalue=20, permskip=0)

print(clientaddperm_query.compile()) # clientaddperm cldbid=16 permid=17276 permvalue=50 permskip=1|permid=21415 permvalue=20 permskip=0
```
