# Discovery-SHEP Stack setup

This doc goes through the process of creating a copy of the Discovery-SHEP stack. Many of the steps below will be generally useful for copying Elastic Beanstalks or databases from an existing deployment.

## Setting up the database

### Create the database

* We have AMI images of the neo4j database configured in AWS. Select the image you want under `EC2 > Images > AMI`, and click `Launch` under `Actions`
* You will be able to configure the vpcs and subnets. Pick the [development|qa|production] vpc and a private subnet.
* You will be able to adjust the inbound rules for the security groups afterwards. Make sure tcp is available to 10.0.0.0/8 for port 7474, 7473, 7687

### Configure the correct graph and start neo4j

1. Copy the database from your computer into the relevant ec2 machine, e.g. :
```scp -i ~/.ssh/nypl-digital-dev graph_v2.4.dump ubuntu@ec2-3-209-56-212.compute-1.amazonaws.com:~ ```
2. Stop the neo4j instance `sudo systemctl stop neo4j`
3. `cd /var/lib/neo4j/data/databases`
4. Remove the old graph.db
		```sudo rm -rf graph.db/``` Alternatively, `mv` graph to somewhere else.
5. Load the new graph db e.g.
```sudo su neo4j -c 'neo4j-admin load --from=/home/ubuntu/graph_v2.3b.dump' ```
6. `sudo systemctl start neo4j`
7. Check the neo4j status `sudo systemctl status neo4j`
8. Remove the scp’ed file


## Copying the Discovery Front End and SHEP API EBs

* Using the `eb save` command, make a copy of the existing resource. For example:
``` eb config save discovery-ui-shep-development ```
This will output the path to the saved configuration, which should be under `.elasticbeanstalk/saved_configs` in the current directory.

* Change the environment variables in the saved config as necessary.

  * For SHEP API you may need to change:
    * `EC2_CONNECT_STRING` to use the ip address of the database you want to connect to
    * `NEO4J_PASSWORD`

  * For Discovery Front End you may need to change:
    * `PLATFORM_API_BASE_URL`
    * `PLATFORM_API_CLIENT_ID` make sure this is encrypted correctly for the environment you are using
    * `SHEP_API` If you hanve't already configured the SHEP_API for your stack, you will need to change this afterwards

* Change the vpc to the development/qa/production vpc

* Change the instance subnet to the private subnet

* Change the load balancer subnet to the public subnet in the same zone as the private subnet

* Security groups and health check path should be fine, but you may need to check them

* Run `eb config put [filename]` with the path to the saved configuration. If you are in the same directory as the code and the configuration is under `.elasticbeanstalk/saved_configs`, you just need the part of the path after `saved_configs`

* Run `eb create [new env name] --cname [new env name] -- cf [config file without .cfg.yml] --profile [profile]`

## Pitfalls

* Ruby/Node version changes can be tricky on EB, so if you are changing those make sure to do it ahead of time
* You may need to run some migrations, which can be done from your local version of the application by first setting local environment variables to match the environment you are targeting.
