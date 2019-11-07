import json
import logging
from typing import Optional, Any

from flask import Flask, request, jsonify

# from . import create_app
from .models import *
from .utils import *
from . import config

ALLOWED_STATUSES = ["ACTIVE","STOPPED","REBOOT"]
def create_app():
	flask_app = Flask(__name__)
	flask_app.config['SQLALCHEMY_DATABASE_URI'] = config.DATABASE_CONNECTION_URI
	flask_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	flask_app.app_context().push()
	db.init_app(flask_app)
	db.create_all()
	return flask_app


app = create_app()


@app.route("/", methods=["GET"])
def indexService():
	return "Hello there! Read <a href=https://documenter.getpostman.com/view/9395373/SW17RafH?version=latest#9e0e3bc6-9b1e-4a2a-aa5a-58bf7119450d>this</a> documentation to start!"

@app.route("/clusters", methods=["GET","POST"])
@app.route("/clusters/<clusterId>", methods=["GET","POST","DELETE"])
def clustersService(**kwargs):
	cluster_id = kwargs.get('clusterId',None)
	if cluster_id and not Cluster.exists(cluster_id):
		return jsonify({"success": False, "error": "cluster does not exist"}), 404
	if request.method == "GET":
		return_json = {"success": True, "clusters": []}
		for obj in Cluster.list(cluster_id):
			return_json['clusters'].append({
				"clusterName": obj.clusterName,
				"clusterId": obj.id,
				"region": obj.region,
				"createdOn": obj.createdOn,
				"updatedOn": obj.updatedOn
			})
		return jsonify(return_json)

	if request.method == "POST":
		return_json = {"success": True}
		body = request.get_json(force=True) if request.get_json(force=True) else {}
		if not cluster_id:
			if not body.get('clusterName',None):
				return jsonify({"success": False, "error": "clusterName required"}), 400
			if Cluster.existsName(body.get('clusterName',None)):
				return jsonify({"success": False, "error": "clusterName already exists"}), 409
		cluster_name = body.get('clusterName')
		region = body.get('region',"Mumbai") if not cluster_id else None
		obj, action = Cluster.addUpdate(cluster_name,region,cluster_id)
		return_json[action] = obj.id
		return jsonify(return_json)

	if request.method == "DELETE":
		success = Cluster.delete(cluster_id)
		return jsonify({"success": success})
#
@app.route("/clusters/<clusterId>/machines", methods=["GET","POST"])
@app.route("/clusters/<clusterId>/machines/<machineId>", methods=["GET","POST","DELETE"])
def machinesService(**kwargs):
	cluster_id = kwargs.get('clusterId', None)
	machine_id = kwargs.get('machineId',None)
	if not Cluster.exists(cluster_id):
		return jsonify({"success": False, "error": "cluster does not exist"}), 404
	if machine_id and not Machine.exists(machine_id):
		return jsonify({"success": False, "error": "machine does not exist"}), 404
	if request.method == "GET":
		return_json = {"success": True, 'machines':[]}
		for obj in Machine.list(cluster_id,machine_id):
			return_json['machines'].append({
				"machineName": obj.machineName,
				"machineId": obj.id,
				"status": obj.status,
				"ipAddress": obj.ipAddress,
				"instanceType": obj.instanceType,
				"tags": obj.tag,
				"createdOn": obj.createdOn,
				"updatedOn": obj.updatedOn
			})
		return jsonify(return_json)

	if request.method == "POST":
		return_json = {"succes": True}
		body = request.get_json(force=True) if request.get_json(force=True) else {}
		machines = body.get("machines",[])
		if machine_id:
			machines = machines[:1]
		for machine in machines:
			machine_name = machine.get('machineName',None)
			status = machine.get('status',None if machine_id else 'ACTIVE')
			ip_address = machine.get('ipAddress',None if machine_id else get_random_ip())
			instance_type = machine.get('instanceType', None if machine_id else 'Standard')
			tag = machine.get('tags',None if machine_id else [])
			if not (machine_name or machine_id):
				return jsonify({"success": False, "error": "machineName required"}), 400
			if Machine.existsName(cluster_id,machine_name):
				return jsonify({"success": False, "error": "machineName already exists"}), 409
			if type(machine.get('tags',[])) != list:
				return jsonify({"success": False, "error": "tags must be a list"}), 400
			if status is not None and status not in ALLOWED_STATUSES:
				return jsonify({"success": False, "error": "status should be one of: 'ACTIVE','STOPPED' or 'REBOOT'"}), 400
			obj = Machine.addUpdate(cluster_id,machine_id,machine_name,status,ip_address,instance_type,tag,machine.get('removeTags',False))

		return jsonify(return_json)

	if request.method == "DELETE":
		success = Machine.delete(machine_id)
		return jsonify({"success":success})

@app.route("/clusters/<clusterId>/tags", methods=["GET"])
@app.route("/clusters/<clusterId>/tags/<tagName>", methods=["GET","POST","DELETE"])
def tagsService(**kwargs):
	cluster_id = kwargs.get('clusterId', None)
	tag_name = kwargs.get('tagName',None)
	if not Cluster.exists(cluster_id):
		return jsonify({"success": False, "error": "cluster does not exist"}), 404
	if request.method == "GET":
		if not tag_name:
			tags = []
			return_json = {"success": True, 'tags':[]}
			for obj in Machine.list(cluster_id):
				tags = tags + obj.tag if obj.tag else []
			return_json['tags'] = list(set(tags))
			return jsonify(return_json)
		else:
			return_json = {"success": True, 'machines':[]}
			for obj in Machine.list(cluster_id,tag=tag_name):
				return_json['machines'].append({
				"machineName": obj.machineName,
				"machineId": obj.id,
				"status": obj.status,
				"ipAddress": obj.ipAddress,
				"instanceType": obj.instanceType,
				"tags": obj.tag,
				"createdOn": obj.createdOn,
				"updatedOn": obj.updatedOn
			})
			return jsonify(return_json)

	if request.method == "POST":
		return_json = {"succes": True}
		body = request.get_json(force=True) if request.get_json(force=True) else {}
		status = body.get('status',None)
		if status not in ALLOWED_STATUSES:
			return jsonify({"success": False, "error": "status should be one of: ACTIVE, STOPPED or REBOOT"}), 400
		Machine.updateStatusByTag(cluster_id,tag_name,status)
		return jsonify(return_json)

	if request.method == "DELETE":
		return_json = {"succes": True}
		status = 'DELETE'
		Machine.updateStatusByTag(cluster_id,tag_name,status)
		return jsonify(return_json)