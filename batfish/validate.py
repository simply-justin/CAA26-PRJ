from pybatfish.client.session import Session

SNAPSHOT_PATH = "batfish/snapshots/test"


def main():
    bf = Session(host="localhost")
    bf.init_snapshot(SNAPSHOT_PATH, name="test", overwrite=True)

    nodes = bf.q.nodeProperties().answer().frame()

    if nodes.empty:
        raise RuntimeError("Batfish validation failed: no nodes found in snapshot")

    required_nodes = {"sleaf01", "sleaf02", "sleaf03"}
    found_nodes = set(nodes["Node"].str.lower())

    missing_nodes = required_nodes - found_nodes

    if missing_nodes:
        raise RuntimeError(f"Batfish validation failed: missing nodes: {missing_nodes}")

    print("Batfish validation successful")
    print(nodes)


if __name__ == "__main__":
    main()
