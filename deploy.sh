#!/bin/bash

LOGFILE='deploy.log'
SERVER='tero@192.168.0.40'

# Base directory for this entire project
BASEDIR=$(cd $(dirname $0) && pwd)

# Copy files to deploy directory
cd $BASEDIR
mkdir -p $BASEDIR/deploy
mkdir -p $BASEDIR/deploy/output
cd ..
cp $BASEDIR/Dockerfile $BASEDIR/deploy
cp $BASEDIR/docker-compose.yml $BASEDIR/deploy
cp $BASEDIR/.env.production $BASEDIR/deploy/.env
cp $BASEDIR/requirements.txt $BASEDIR/deploy
cp $BASEDIR/run_task.sh $BASEDIR/deploy
cp -r $BASEDIR/helpers $BASEDIR/deploy
cp $BASEDIR/config.py $BASEDIR/deploy
cp $BASEDIR/get_forecast.py $BASEDIR/deploy


# EXCLUDES=$BASEDIR'/excludes.txt'


SOURCE_DIR='deploy'
# SOURCE_PATH=$BASEDIR'/'$SOURCE_DIR
SOURCE=$BASEDIR'/'$SOURCE_DIR'/'

TARGET_DIR='~/services/pv-forecast'
# echo $TARGET_DIR

# #create folder if doesn't exist
ssh $SERVER 'mkdir -p '$TARGET_DIR

# #TARGET='tero@192.168.111.131:'$TARGET_PATH
TARGET=$SERVER':'$TARGET_DIR

rsync -av --delete $SOURCE $TARGET >> $LOGFILE