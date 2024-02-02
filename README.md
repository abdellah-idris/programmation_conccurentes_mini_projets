# IRC & Game Of Life
These university projects offer opportunities to explore topics such as multithreading, network programming, user interfaces, and synchronization.

## University Project 1: Conway's Game of Life

This university project focuses on simulating Conway's Game of Life, which represents the evolution of a population of cells within a two-dimensional grid. 

- Develop a version where each cell in the grid is assigned to its own thread, and these threads calculate the state of their respective cells.

- Ensure proper **synchronization between threads** to prevent any cell from calculating the state for time step n + 1 until others have finished calculating for time step n.

## Usage


#### Launch Game
```bash
python game_of__life/game_of_life.py
```


## University Project 2: Online Chat Server
This university project involves the development of an online chat server using Python. The server implements an Internet Relay Chat (IRC) system, allowing users to communicate in real-time by sending messages and commands to the server.

- Develop a **Multi server IRC**, Inclusing basic commands including /away, /help, /invite, /join, /list, /msg, and /names.


## Usage


#### Launch Server
You can launch multiple servers at once.
```bash
python irc/server.py <port1> port2 port3 ...
```
```bash
python irc/server.py 8080 8081
```

#### Launch Client
Server port match an up server, otherwise server is off messge will be showed.
```bash
python irc/client.py <user_name> <port_number>
```

```bash
python irc/client.py dola 8081
```
