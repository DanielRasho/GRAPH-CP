<div>
    <h1 align="center"> GRAPH-CP 🎨</h1>
    <h3 align="center"> 
        A UML Generator MCP server
    </h3>
</div>

An MCP server that brings your IA agent drawing capabilities to generate plots and graphs of various types: graphs, entity-relation, UML classes, trees, by just describing your needs. Supports:

- Generation of PNG and .DOT files in your filesystem.
- Specify Image file size.
- Specify output folder.

## Installation

1. Download the source code
```bash
git clone https://github.com/DanielRasho/GRAPH-CP
```
2. Install graphviz (used for rendering diagrams) and uv.
```bash
# Ubuntu
sudo apt install graphviz
# Arch
sudo pacman -S graphviz
# MacOS
brew install graphviz
# Windows
# Download the executables in https://graphviz.org/download/
```

3. Then add the execution commands to your client config:
```json
{
  "servers": [
    {
      "name": "GraphCP",
      "command": "uv",
      "args": [
        "--directory",
        "<SOURCE CODE ABSOLUTE DIRECTORY>", 
        "run",
        "server.py"
      ],
      "description": "Graph generator",
      "env": {
      }
    }
  ]
}
```

4. Add the configuration 

## Examples

**Company diagram**
```
We want to show how people in a small company relate to each other.  
There are 13 people in total.  

Some belong to the technical side:  
- One person is responsible for guiding the development team (a tech lead).  
- There are 5 developers who usually follow the tech lead’s guidance.  
- There is also someone who looks after the development process itself (a Scrum Master).  
- Another person is in charge of deciding what should be built (a Product Owner).  

Others are on the business side:  
- There are 5 sellers who are mostly focused on bringing customers and handling sales.  

Think of it as an organigram, but the exact arrangement is not fixed.  
You can assume that roles with responsibility (like Product Owner, Tech Lead, or Scrum Master) should somehow appear more “central” or “above” the rest.  
Developers tend to be grouped under whoever coordinates them, and sellers are grouped together but not mixed with the tech people.  
The Product Owner may have connections to both technical and sales sides.  

The visual style is up to interpretation:  
- Maybe leadership roles stand out with stronger shapes or colors.  
- People in the same kind of role (developers or sellers) should look visually grouped.  
```

**Directed graph**
```
yes chat can you help me generate a directed grap with this code i would like the nodes to be red and the edges blue

A = [
  [0,1,1,0,0,0],
  [1,0,1,1,0,0],
  [1,1,0,0,1,0],
  [0,1,0,0,1,1],
  [0,0,1,1,0,1],
  [0,0,0,1,1,0],
]
```

**Entity relation**

```
now can you generate a entityt relation diagram for me knowing this sql schema? 

-- Users of the system
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Products available for purchase
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL DEFAULT 0
);

-- Orders placed by users
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    user_id INT NOT NULL,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Items within each order
CREATE TABLE order_items (
    order_item_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL CHECK (quantity > 0),
    price DECIMAL(10, 2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- Payments made for orders
CREATE TABLE payments (
    payment_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    method VARCHAR(30) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
);
```