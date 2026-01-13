#!/usr/bin/env bash
K8S_OPS_REPO_BRANCH=master
K8S_OPS_REPO_SLUG=OpenBudget/budgetkey-k8s
DEPLOY_VALUES_IMAGE_PROP=image
DEPLOY_YAML_UPDATE_FILE=values.auto-updated.yaml
DEPLOY_GIT_EMAIL=budgetkey-deployer@null.void
DEPLOY_GIT_USER=budgetkey-deployer

DEPLOY_COMMIT_MESSAGE="automatic update of budgetkey-mcp"
DEPLOY_VALUES_CHART_NAME=mcp
DOCKER_IMAGE=budgetkey/budgetkey-mcp


if [ "${1}" == "install" ]; then
    mkdir -p $HOME/bin &&
    curl -L https://raw.githubusercontent.com/OriHoch/travis-ci-operator/master/travis_ci_operator.sh > $HOME/bin/travis_ci_operator.sh &&\
    bash $HOME/bin/travis_ci_operator.sh init
    [ "$?" != "0" ] && exit 1
    ([ -z "${DOCKER_USER}" ] || ! $HOME/bin/travis_ci_operator.sh docker-login) && echo WARNING! Failed to login to Docker
    exit 0

elif [ "${1}" == "script" ]; then
    docker pull "${DOCKER_IMAGE}:latest"
    ! docker build --cache-from "${DOCKER_IMAGE}:latest" -t "${DOCKER_IMAGE}:latest" . && exit 1
    exit 0

elif [ "${1}" == "deploy" ]; then
    TAG="${GITHUB_SHA}"
    docker tag "${DOCKER_IMAGE}:latest" "${DOCKER_IMAGE}:${TAG}" &&\
    docker push "${DOCKER_IMAGE}:latest" &&\
    docker push "${DOCKER_IMAGE}:${TAG}"
    [ "$?" != "0" ] && exit 1
    echo
    echo "${DOCKER_IMAGE}:latest"
    echo "${DOCKER_IMAGE}:${TAG}"
    echo
    exit 0

elif [ "${1}" == "bump" ]; then
    TAG="${GITHUB_SHA}"
    docker run -e CLONE_PARAMS="--branch ${K8S_OPS_REPO_BRANCH} https://github.com/${K8S_OPS_REPO_SLUG}.git" \
               -e YAML_UPDATE_JSON='{"'"${DEPLOY_VALUES_CHART_NAME}"'":{"'"${DEPLOY_VALUES_IMAGE_PROP}"'":"'"${DOCKER_IMAGE}:${TAG}"'"}}' \
               -e YAML_UPDATE_FILE="${DEPLOY_YAML_UPDATE_FILE}" \
               -e GIT_USER_EMAIL="${DEPLOY_GIT_EMAIL}" \
               -e GIT_USER_NAME="${DEPLOY_GIT_USER}" \
               -e GIT_COMMIT_MESSAGE="${DEPLOY_COMMIT_MESSAGE}" \
               -e PUSH_PARAMS="https://${GITHUB_TOKEN}@github.com/${K8S_OPS_REPO_SLUG}.git ${K8S_OPS_REPO_BRANCH}" \
               orihoch/github_yaml_updater
    [ "$?" != "0" ] && echo failed github yaml update && exit 1
    exit 0
fi

echo unexpected failure
exit 1
