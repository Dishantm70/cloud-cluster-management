import flask_sqlalchemy
from sqlalchemy.dialects.postgresql import ARRAY
import uuid

db = flask_sqlalchemy.SQLAlchemy()


class Cluster(db.Model):
	__tablename__ = 'Cluster'
	id = db.Column(db.String(50), primary_key=True)
	clusterName = db.Column(db.String(100), unique=True)
	region = db.Column(db.String, default='Mumbai')
	createdOn = db.Column(db.DateTime, server_default=db.func.now())
	updatedOn = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

	@classmethod
	def exists(cls,clusterId):
		return cls.query.filter_by(id=clusterId).first()

	@classmethod
	def existsName(cls,clusterName):
		return cls.query.filter_by(clusterName=clusterName).first()

	@classmethod
	def list(cls, clusterId=None):
		obj = cls.query.all() if not clusterId else cls.query.filter_by(id=clusterId).all()
		return obj if obj else []


	@classmethod
	def addUpdate(cls,clusterName,region,clusterId):
		obj = None
		action = 'UPDATED'
		if clusterId:
			obj = cls.query.filter(cls.id==clusterId).first()
		if not obj:
			action = 'ADDED'
			obj = cls(id=str(uuid.uuid4())[:15])
		if clusterName:
			obj.clusterName=clusterName
		if region:
			obj.region=region
		db.session.add(obj)
		db.session.commit()
		return obj, action

	@classmethod
	def delete(cls,clusterId):
		obj = cls.query.filter(cls.id==clusterId).first()
		if obj:
			for machine in Machine.list(clusterId):
				db.session.delete(machine)
			db.session.delete(obj)
			db.session.commit()
			return True
		return False

class Machine(db.Model):
	__tablename__ = 'Machine'
	clusterId = db.Column(db.String(50), db.ForeignKey('Cluster.id'))
	id = db.Column(db.String(50), primary_key=True)
	machineName = db.Column(db.String(100))
	status = db.Column(db.String(20))
	ipAddress = db.Column(db.String(20), primary_key=True)
	instanceType = db.Column(db.String(20), primary_key=True)
	tag = db.Column(ARRAY(db.String))
	createdOn = db.Column(db.DateTime, server_default=db.func.now())
	updatedOn = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

	@classmethod
	def exists(cls,machineId):
		return cls.query.filter_by(id=machineId).first()

	@classmethod
	def existsName(cls,clusterId,machineName):
		return cls.query.filter_by(clusterId=clusterId,machineName=machineName).first()\

	@classmethod
	def existsIp(cls,ipAddress):
		return cls.query.filter_by(ipAddress=ipAddress).first()

	@classmethod
	def list(cls, clusterId,machineId=None,tag=None):
		obj = cls.query.filter_by(clusterId=clusterId).all() \
			if not machineId and not tag \
			else cls.query.filter_by(clusterId=clusterId,id=machineId).all() if not tag \
			else cls.query.filter(cls.clusterId==clusterId).filter(Machine.tag.any(tag)).all()
		return obj if obj else []

	@classmethod
	def addUpdate(cls,cluster_id,machineId=None,machineName=None,status=None,ipAddress=None,instanceType=None,tag=None,removeTags=False):
		obj = None
		if machineId:
			obj = cls.query.filter(cls.id==machineId).first()
		if not obj:
			obj = cls(id=str(uuid.uuid4())[:15])
		obj.clusterId = cluster_id
		if machineName:
			obj.machineName=machineName
		if status:
			obj.status=status
		if ipAddress:
			obj.ipAddress=ipAddress
		if instanceType:
			obj.instanceType=instanceType
		if tag:
			if removeTags:
				obj.tag = list(set(obj.tag if obj.tag else []) - set(tag))
			else:
				obj.tag=list(set(obj.tag if obj.tag else [] + tag))
		db.session.add(obj)
		db.session.commit()
		return obj

	@classmethod
	def delete(cls,machineId):
		obj = cls.query.filter(cls.id==machineId).first()
		if obj:
			db.session.delete(obj)
			db.session.commit()
			return True
		return False

	@classmethod
	def deleteTags(cls,clusterId,machineId,tags):
		obj = cls.query.filter(cls.id==machineId,clusterId=clusterId).first()
		if obj:
			obj.tag = list(set(obj.tag if obj.tag else []) - set(tags))
			db.session.add(obj)
			db.session.commit()
			return True
		return False

	@classmethod
	def updateStatusByTag(cls,clusterId,tag,status):
		objs = cls.query.filter(cls.tag.any(tag)).filter(cls.clusterId==clusterId).all()
		if objs:
			for obj in objs:
				if status == 'DELETE':
					db.session.delete(obj)
				else:
					obj.status = status
					db.session.add(obj)
				db.session.commit()
			return True
		return False
