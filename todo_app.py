from flask import Flask, render_template, request, redirect, url_for, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
import sys

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://sh_ubuntu:93water94@localhost:5432/todoapp_new'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# expire_on_commit is set to true by default, such that all instances will expire after each commit
# if needed, we can set session_options={"expire_on_commit":False} but that can have unintended side effects
# e.g. db = SQLAlchemy(app, session_options={"expire_on_commit":False})
db = SQLAlchemy(app)

migrate = Migrate(app, db) # create an instance of the Migrate class to link to command line scripts

class ToDo(db.Model):
    __tablename__='newww_todo'
    id = db.Column(db.Integer,primary_key=True)
    title = db.Column(db.String(),nullable=False)
    description = db.Column(db.String(),nullable=True)
    completed = db.Column(db.Boolean, nullable=False, default=False)
    deadline = db.Column(db.DateTime,nullable=True)
    list_id = db.Column(db.Integer, db.ForeignKey('todolists.id'), nullable=False)

    def __repr__(self):
        return f'<To Do List {self.id}: {self.name}>'

class ToDoList(db.Model):
    __tablename__ ='todolists'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(), nullable=False)
    description = db.Column(db.String(), nullable=True)
    todos = db.relationship('ToDo', backref='list', lazy=True, cascade = 'all, delete-orphan') # lazy=True by default

    def __repr__(self):
        return f'<To Do Item {self.id}: {self.title} by {self.deadline}>'

# db.create_all()

#todo = ToDo(title='Finish Lesson 5')
#todo2 = ToDo(title='Complete first project')
#todo3 = ToDo(title='Sleep')
#db.session.add_all([todo,todo2,todo3])
    
#db.session.commit()

# define what template to show to users when users visit the homepage
# by default, flask looks for your templates in the templates folder

### method 1 of data input : synchronous request from form input
### in this case the form in index.html will have action and methods defined
### and server will handle it using the below function when request is received

# @app.route('/create-todo',methods=['POST'])
#def create_sync():
#    todo_title=request.form.get('title')
#    todo_desc=request.form.get('description')
#    new_todo=ToDo(title=todo_title,description=todo_desc)
#    db.session.add(new_todo)
#    db.session.commit()
#    return redirect(url_for('index')) # this refreshes the page

### method 2 of data input: acynchronous request from form input
### client will fetch response from server after completion and handles the response
### server will not define how the response will be handled and how the view is updated

@app.route('/list/create',methods=['POST'])
def createlist_unsync():
    listname=request.get_json()['listname']
    listdescription=request.get_json()['listdescription']    
    
    # initialise the variables to be used
    error=False
    body={}
    
    try:
        new_todolist=ToDoList(name=listname,description=listdescription)
        db.session.add(new_todolist)
        db.session.commit()
        body['id']=new_todolist.id
        body['name']=new_todolist.name
        body['description']=new_todolist.description
    except:
        error=True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close() # return connection to connection pool for more efficient resource mgmt
    if error:
        abort(400)
    else:
        return jsonify(body)

@app.route('/lists/<listID>/delete',methods=['DELETE'])
def delete_list(listID):
    error=False
    try:
        list=ToDoList.query.get(listID)
        for todo in list.todos:
            db.session.delete(todo)
            
        db.session.delete(list)
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return jsonify({'success': True})

@app.route('/lists/<listID>/set-completed',methods=['POST'])
def list_completed(listID):
    error=False
    try:
        list = ToDoList.query.get(listID)
        for todo in list.todos:
            todo.completed = True
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return jsonify({'success': True})

@app.route('/lists/<listID>/todo/create',methods=['POST'])
def create_unsync(listID):
    title=request.get_json()['title']
    description=request.get_json()['description']   
    
    # initialise the variables to be used
    error=False
    body={}
    
    try:
        new_todo=ToDo(title=title,description=description,list_id=listID)
        db.session.add(new_todo)
        db.session.commit()
        body['id']=new_todo.id
        body['title']=new_todo.title
        body['description']=new_todo.description
    except:
        error=True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close() # return connection to connection pool for more efficient resource mgmt
    if error:
        abort(400)
    else:
        return jsonify(body)

@app.route('/todo/<todoID>/set-completed',methods=['POST'])
def set_completed(todoID):
    complete_status = request.get_json()['completed']
    error=False
    try:
        todo = ToDo.query.get(todoID)
        todo.completed = complete_status
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return redirect(url_for('index'))

@app.route('/todo/<todoID>/delete',methods=['DELETE'])
def delete_todo(todoID):
    error=False
    try:
        ToDo.query.filter_by(id=todoID).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        abort(500)
    else:
        return jsonify({'success': True})

@app.route('/lists/<list_id>')
def get_todo_list(list_id):
    return render_template('index.html',
    lists=ToDoList.query.order_by('id'),
    activelist=ToDoList.query.get(list_id),
    todos=ToDo.query.filter_by(list_id=list_id).order_by('id').all())

@app.route('/')
def index():
    return redirect(url_for('get_todo_list',list_id=1)) # can consider how to set this to a variable
