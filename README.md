# Python Messenger
Python Messenger is a small, functional messaging application written in Python using sockets. It allows users to chat with each other, with messages saved in a database and loaded dynamically on the client's request. Note that this version does not include message or user data encryption.

## Features
- User Accounts: Users can create and log into accounts.
- Chat Management: The server manages user chats and stores messages.
- Dynamic Loading: Messages are saved in a database and loaded dynamically when users enter or scroll through chats.
- Configuration: Clients can save login data and themes in a configuration file.

## Running
### Server
The server manages the chats between user accounts. User accounts are saved in a database of the server. Clients can log into an account and retrieve the messages from these chats.

Starting the server:
`python src/server.py [options]`

Options:
- `--database [path]`: Specify the path to the database to store messages and accounts. Default: `data/server.db`

### Client
The client connects to the server. Clients can create or log into accounts when connected to the server to send and retrieve messages. Clients may have a config file to save the last used log in data and theme but not their chats.

Starting a client:
`python src/client.py [options]`

Options:
- `--config [path]`:  Specify the path to the .config file to save login data and theme. Default: `data/client.config`
