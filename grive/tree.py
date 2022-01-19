class Node:
    def __init__(self, key):
        self.key = key
        self.child = []


def newNode(key):
    temp = Node(key)
    return temp


def LevelOrderTraversal(root):
    if (root == None):
        return;

    # Standard level order traversal code
    # using queue
    q = []  # Create a queue
    q.append(root);  # Enqueue root
    while (len(q) != 0):

        n = len(q);

        # If this node has children
        while (n > 0):

            # Dequeue an item from queue and print it
            p = q[0]
            q.pop(0);
            print(p.key, end='->')
            if len(p.child) > 0:
                for e in p.child:
                    print(e.key.get("name"), end=",")
            print()

            # Enqueue all children of the dequeued item
            for i in range(len(p.child)):
                q.append(p.child[i]);
            n -= 1

        print()  # Print new line between two levels


def add_node(root, index, value):
    if (root == None):
        return;
    # Standard level order traversal code
    # using queue
    q = []  # Create a queue
    q.append(root);  # Enqueue root
    while (len(q) != 0):
        n = len(q);
        # If this node has children
        while (n > 0):
            p = q[0]
            q.pop(0);
            tmp_key = {'id': p.key['id'], 'name': p.key['name']}
            if tmp_key == index:
                tmp_value = {'id': value['id'], 'name': value['name']}
                if len(list(filter(lambda e: {'id': e.key['id'], 'name': e.key['name']} == tmp_value, p.child))) == 0:
                    p.child.append(newNode(value))

            # Enqueue all children of the dequeued item
            for i in range(len(p.child)):
                q.append(p.child[i]);
            n -= 1


def get_direct_sub_node(root, index):
    if root is None:
        return

    # Standard level order traversal code
    # using queue
    q = []  # Create a queue
    q.append(root)  # Enqueue root
    while len(q) != 0:

        n = len(q)

        # If this node has children
        while n > 0:
            p = q[0]
            q.pop(0)
            if index['id']:  # if id != None
                if index['id'] == p.key['id']:
                    return p.key, p.child
            else: 
                tmp_key = {"id": p.key["id"], "name": p.key["name"]}
                if tmp_key == index:
                    return p.key, p.child
   
            # Enqueue all children of the dequeued item
            for i in range(len(p.child)):
                q.append(p.child[i])
            n -= 1

    return None


def find_node_by_canonicalPath(root, path):
    if root is None:
        return
    q = []  # Create a queue
    q.append(root)  # Enqueue root
    while len(q) != 0:
        n = len(q)
        # If this node has children
        while n > 0:
            p = q[0]
            q.pop(0)
            if p.key.get("canonicalPath") == path:
                return p

            # Enqueue all children of the dequeued item
            for i in range(len(p.child)):
                q.append(p.child[i])
            n -= 1
    return None
