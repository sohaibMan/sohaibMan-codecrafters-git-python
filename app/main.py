import sys
import os
import zlib


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

    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
