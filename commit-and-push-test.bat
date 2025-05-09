@echo off
git add .github/workflows/test-workflow.yml
git commit -m "Add test workflow with upload-artifact@v1"
git push origin master
