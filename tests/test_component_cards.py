def test_package_imports():
    import bioscaffold

    assert bioscaffold.__all__ == ["BioCell", "CellRole", "LifecyclePhase"]
