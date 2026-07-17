from grimmcraft_cli.main import main


def test_main_default(capsys) -> None:
    exit_code = main([])
    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "Hello, World!"


def test_main_with_name(capsys) -> None:
    main(["Grimm"])
    assert capsys.readouterr().out.strip() == "Hello, Grimm!"
