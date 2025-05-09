@echo off
git add .github/workflows/price-feed.yml
git rm .github/workflows/simple-test.yml
git commit -m "Remove simple-test workflow and ensure other workflows run automatically"
git push origin master
