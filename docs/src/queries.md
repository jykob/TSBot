# Queries

TSBot implements a query builder to ease the use of sending commands to the server.  
In this chapter you will learn how to use the query system in TSBot

## Creating a query object

Creating a query object is as easy as calling a function.  
This can be achieved by importing [query](tsbot.query_builder.query) from `tsbot` and calling it with the desired command.

```
from tsbot import query

clientlist_query = query("clientlist")
```

This creates [TSQuery](tsbot.query_builder.TSQuery) object which you can manipulate to build out your command.

## Manipulating TSQuery objects

## Examples

Section to show examples of using queries
