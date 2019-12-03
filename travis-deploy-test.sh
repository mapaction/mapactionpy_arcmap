if ["$TRAVIS_BRANCH" -eq "master"];
then
  export TRAVIS_TAG="$TRAVIS_BRANCH"
fi