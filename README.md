# un editor de istorie care iti da puterea sa fii eminescu cu commit urile slash istoria de pe github

# aka (uedicidpsfeccusidpg)

Used to generate contribution history art. This can also generate exact total profile commits.

![screenshot of contribution graph](assets/contribution-screenshot.png)

Basic usage: First download `un-editor-de-istorie-care-iti-da-puterea-sa-fii-eminescu-cu-commit-urile-slash-istoria-de-pe-github.py` from this git repo, after that, using a pattern file (.uedicidpsfeccusidpg, for example checkout `pattern.uedicidpsfeccusidpg`). Generate a new git repo by specifying the `-o {OUTPUT_LOCATION}` flag. You can then push that to your github account. I recomend using `gh repo create --public --push --source=.` to push your repo to github and `gh repo delete --yes` to delete it.

example usage:
```
py .\un-editor-de-istorie-care-iti-da-puterea-sa-fii-eminescu-cu-commit-urile-slash-istoria-de-pe-github.py .\pattern.uedicidpsfeccusidpg -o "github-history-art" --commits-per-pixel 20
```

This will make a repository with the pixel art with 20 commits per pixel.

If you instead wish to achieve a certain commit count you can use the `--total-commit-count` flag instead of `--commits-per-pixel`. You should also probably use the `--user` flag when using `--total-commit-count`. 

For example this is how I can achieve 69420 commits:
```
py .\un-editor-de-istorie-care-iti-da-puterea-sa-fii-eminescu-cu-commit-urile-slash-istoria-de-pe-github.py .\pattern.uedicidpsfeccusidpg -o "github-history-art" --total-commit-count 69420 --user insertokname
```

If you want to delete the existing repository in the specified location use `--overwrite`.