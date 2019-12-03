echo "In ./travis-deploy-test.sh"
if [ "${TRAVIS_BRANCH,,}" -eq "master" ];
then
  echo "On master branch"
  export TRAVIS_TAG="$TRAVIS_BRANCH"
fi