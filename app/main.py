import hashlib
import sys
import os
import zlib

git_ignore = '.git'


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")

    elif command == "cat-file" and len(sys.argv) == 4 and sys.argv[2] == "-p":
        # Verify the existence of .git/objects
        if not os.path.isdir(".git/objects"):
            print("Failed to find .git/objects directory. Make sure you run 'git init' before.", file=sys.stderr)
            sys.exit(1)

        blob_sha = sys.argv[3]
        object_dir = blob_sha[:2]
        object_file = blob_sha[2:]
        object_path = os.path.join(".git", "objects", object_dir, object_file)

        if not os.path.isfile(object_path):
            print("Failed to open object file.", file=sys.stderr)
            sys.exit(1)

        # Read the object file
        with open(object_path, "rb") as f:
            compressed_data = f.read()

        try:
            raw = zlib.decompress(compressed_data)
            header, content = raw.split(b"\0", maxsplit=1)
            print(content.decode(encoding="utf-8"), end="")
        except zlib.error as e:
            print(f"Error decompressing the object file: {e}", file=sys.stderr)
            sys.exit(1)
    elif command == "hash-object" and len(sys.argv) == 4 and sys.argv[2] == "-w":
        file_name = sys.argv[3]
        try:
            with open(file_name, "rb") as f:
                content = f.read()
                header = f"blob {len(content)}\0".encode('utf-8')
                data = header + content
                blob_sha = hashlib.sha1(data).hexdigest()
                compressed_data = zlib.compress(data)

                object_dir = blob_sha[:2]
                object_file = blob_sha[2:]

                object_path = os.path.join(".git", "objects", object_dir, object_file)

                os.makedirs(os.path.dirname(object_path))

                with open(object_path, "wb") as blob_file:
                    blob_file.write(compressed_data)

                print(blob_sha)

        except FileNotFoundError as e:
            print(f"Failed to find .git/objects directory. Make sure you run 'git init' before. {e}", file=sys.stderr)
            sys.exit(1)

    elif command == "ls-tree" and len(sys.argv) == 4 and sys.argv[2] == "--name-only":
        tree_sha = sys.argv[3]
        object_dir = tree_sha[:2]
        object_file = tree_sha[2:]
        object_path = os.path.join(".git", "objects", object_dir, object_file)
        with open(object_path, 'rb') as f:
            compressed_data = f.read()
            raw = zlib.decompress(compressed_data)
            header, content = raw.split(b"\0", maxsplit=1)
            if not header.startswith(b"tree"):
                raise print(f"Object file does not exist: {object_path}")

            while content:
                # Extract the mode (e.g., '100644' or '40000')
                mode, _, content = content.partition(b' ')
                # Extract the filename
                filename, _, content = content.partition(b'\0')
                # Add folders and files
                if mode.decode() in ('100644', '40000'):
                    # for files
                    print(filename.decode())

                # Remove the SHA-1 from the remaining content
                content = content[20:]
    elif command == "write-tree":
        print(write_tree('.'))
    else:
        raise RuntimeError(f"Unknown command #{command}")


def write_tree(path):
    tree_content = b''
    git_path = os.path.join('.', '.git')

    # Iterate over the files/directories in the working directory
    for entry in sorted(os.listdir(path)):
        if entry in git_ignore:
            continue

        full_path = os.path.join(path, entry)

        isDir = os.path.isdir(full_path)

        if isDir:
            # If the entry is a directory, recursively create a tree object and record its SHA hash
            mode = '40000'
            sha1_hash = write_tree(full_path)
        else:
            # If the entry is a file, create a blob object and record its SHA hash
            mode = '100644'

            # Step 1: Read the file content
            with open(full_path, "rb") as f:
                file_content = f.read()

            # Step 2: Prepare the blob header
            header = f"blob {len(file_content)}\0".encode()

            # Step 3: Concatenate header and content
            blob_data = header + file_content

            # Step 4: Compute the SHA-1 hash
            sha1_hash = hashlib.sha1(blob_data).hexdigest()

            # Step 4: Compute the SHA-1 hash
            write_object(sha1_hash, blob_data, git_path)


        tree_entry = f"{mode} {entry}\0".encode() + bytes.fromhex(sha1_hash)
        tree_content += tree_entry

    header = f"tree {len(tree_content)}\0".encode()
    tree_object = header + tree_content

    # Once you have all the entries and their SHA hashes, write the tree object to the .git/objects directory
    tree_sha = hashlib.sha1(tree_object).hexdigest()

    write_object(tree_sha, tree_object, git_path)

    return tree_sha


def write_object(sha, content, git_path):
    """Write an object to the .git/objects directory."""
    object_dir = os.path.join(git_path, 'objects', sha[:2])
    if not os.path.exists(object_dir):
        os.makedirs(object_dir)

    object_path = os.path.join(object_dir, sha[2:])
    if not os.path.exists(object_path):
        with open(object_path, "wb") as f:
            f.write(zlib.compress(content))


if __name__ == "__main__":
    main()
