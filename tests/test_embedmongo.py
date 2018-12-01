from embedmongo import __version__, main

def test_version():
    main.main()
    assert __version__ == '0.1.0'
