# Publish the prepared source

The reviewed source archive and offline Git bundle are under `submission/`. They exclude API keys, databases, downloaded transcripts/models, dependencies and private local chats. The package contains only source, tests, documentation and public-corpus evaluation examples. Run the packager again after changing source files; a previous bundle is a snapshot, not a live view.

Create an empty **public** repository in your GitHub account. Use the actual URL GitHub gives you, then clone the reviewed bundle into a separate directory and push it:

```bash
git clone /absolute/path/to/submission/lenny-growth-assistant.bundle lenny-submission
cd lenny-submission
git remote remove origin
git remote add origin https://github.com/YOUR_OWNER/YOUR_REPOSITORY.git
git push -u origin main
```

Use GitHub's normal credential manager or SSH authentication. Do not place a token in a command, URL, source file or video. Publication requires the correct account/repository and authenticated access; no public repository has been claimed to exist yet.

After publishing, use a new directory to test exactly what the evaluator receives:

```bash
git clone https://github.com/YOUR_OWNER/YOUR_REPOSITORY.git evaluator-check
cd evaluator-check
./setup.sh
./start.sh
```

Follow the prerequisites in README. This test must install its own dependencies, rebuild the public corpus and use its own local data. Check Ollama selection, a question/follow-up, a saved essay and both artifact formats. Stop startup with Ctrl+C, then run `./scripts/check.sh`. Record the actual public URL and this verification in `submission-checklist.md`.

Record and upload the camera-enabled demo using `demo-script.md`. Check the public repository and video links from a signed-out browser, then submit their actual URLs through the assignment form. A local archive, private repository or prepared recording script does not fulfill those external deliverables.
