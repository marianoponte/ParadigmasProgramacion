#!/usr/bin/env python
import csv
import re
from flask import Flask, render_template, redirect, url_for, flash, session
from flask_bootstrap import Bootstrap
from forms import ClienteForm, ProductoForm, LoginForm, RegistrarForm

app = Flask(__name__)
bootstrap = Bootstrap(app)

app.config['SECRET_KEY'] = 'secret key'

#Esta funcion captura el indice de cada columna sin importar el orden en que se encuentren dichas columnas
def indices():
	with open('registros.csv') as archivo:
		archivo_csv = csv.reader(archivo)
		registro = next(archivo_csv)
		dicindices = {}
		
		dicindices['indice_codigo'] = registro.index('CODIGO')
		dicindices['indice_producto'] = registro.index('PRODUCTO')
		dicindices['indice_cliente'] = registro.index('CLIENTE')
		dicindices['indice_cantidad'] = registro.index('CANTIDAD')
		dicindices['indice_precio'] = registro.index('PRECIO')

	return dicindices
			
# Esta funcion valida y devuelve si el archivo .csv es valido, y ademas los errores encontrados si la validacion fue invalida
def validararchivo():
	dicindices = indices()
	try:
		with open('registros.csv') as archivo:
			archivo_csv = csv.reader(archivo)
			registro = next(archivo_csv)
			registro = next(archivo_csv)
			valido = True
			errordevalidacion = set([])
			patron = re.compile(r"^[A-Z]{3}\d{3}$")
			while registro:
				if patron.search(registro[dicindices['indice_codigo']]) == None:
					valido = False
					errordevalidacion.add("Codigo de producto invalido")
				if len(registro) != 5 and registro != None:
					valido = False
					errordevalidacion.add("Cantidad de columnas invalidas")
				try: 
					int(registro[dicindices['indice_cantidad']])
				except:
					valido = False
					errordevalidacion.add("Columna cantidad no tiene un valor entero")
				try:
					float(registro[dicindices['indice_precio']])
					if registro[dicindices['indice_precio']].find(".") == -1:
						valido = False
						errordevalidacion.add("Columna precio no tiene un valor decimal")
				except:
					valido = False
					errordevalidacion.add("Columna precio no tiene un valor decimal")
				registro = next(archivo_csv, None)



	except FileNotFoundError:
		valido = False
		errordevalidacion = "No se encontró el archivo a procesar"

	return [valido, errordevalidacion]

#Esta funcion devuelve la lista de clientes que coinciden con los 3 o mas caracteres ingresados en la busqueda
def listadodeclientesamostrar(largocliente,cliente):
	dicindices = indices()
	largocliente = int(largocliente)
	listadeclientesamostrar = set([])
	with open('registros.csv') as archivo:
		archivo_csv = csv.reader(archivo)
		registro = next(archivo_csv)
		registro = next(archivo_csv)
		while registro:
			if cliente == registro[dicindices['indice_cliente']][:largocliente]:
				listadeclientesamostrar.add(registro[dicindices['indice_cliente']])
			registro = next(archivo_csv, None)
	return listadeclientesamostrar

#Esta funcion devuelve la lista de productos que coinciden con los 3 o mas caracteres ingresados en la busqueda
def listadodeproductosamostrar(largoproducto,producto):
	dicindices = indices()
	largoproducto = int(largoproducto)
	listadeproductosamostrar = set([])
	with open('registros.csv') as archivo:
		archivo_csv = csv.reader(archivo)
		registro = next(archivo_csv)
		registro = next(archivo_csv)
		while registro:
			if producto == registro[dicindices['indice_producto']][:largoproducto]:
				listadeproductosamostrar.add(registro[dicindices['indice_producto']])
			registro = next(archivo_csv, None)
	return listadeproductosamostrar

# Devuelve un template informando error 404
@app.errorhandler(404)
def no_encontrado(e):
    return render_template('404.html'), 404

# Devuelve un template informando error 500
@app.errorhandler(500)
def error_interno(e):
    return render_template('500.html'), 500

#Index previo al ingreso del login
@app.route('/')
def index():
	return render_template('index.html')

# Index posterior al ingreso login
@app.route('/index')
def indexprincipal():
	return render_template('index2.html')

#Funcion para el login
@app.route('/ingresar', methods=['GET', 'POST'])
def ingresar():
    formulario = LoginForm()
    if formulario.validate_on_submit():
        with open('usuarios.csv') as archivo:
            archivo_csv = csv.reader(archivo)
            registro = next(archivo_csv)
            validacion = validararchivo()
            while registro:
                if formulario.usuario.data == registro[0] and formulario.password.data == registro[1]:
                    flash('Bienvenido')
                    session['username'] = formulario.usuario.data
                    if validacion[0] == True:
                    	return render_template('ingresado.html')
                    else: 
                    	return render_template('errordearchivo.html', error=validacion[1])
                registro = next(archivo_csv, None)
            else:
                flash('Revisá nombre de usuario y contraseña')
                return redirect(url_for('ingresar'))
    return render_template('login.html', formulario=formulario)

#Funcion para registro de nuevo usuario
@app.route('/registrar', methods=['GET', 'POST'])
def registrar():
    formulario = RegistrarForm()
    if formulario.validate_on_submit():
        if formulario.password.data == formulario.password_check.data:
            with open('usuarios.csv','a+') as archivo:
                archivo_csv = csv.writer(archivo)
                registro = [formulario.usuario.data,formulario.password.data]
                archivo_csv.writerow(registro)
            flash('Usuario creado correctamente')
            return redirect(url_for('ingresar'))
        else:
            flash('Las passwords no matchean')
    return render_template('registrar.html', form=formulario)

#Funcion para Salir del sistema (Logout)
@app.route('/logout', methods=['GET'])
def logout():
    if 'username' in session:
        session.pop('username')
        return render_template('logged_out.html')
    else:
        return redirect(url_for('index'))

#Funcion Para ultimas ventas realizadas
@app.route('/ventas', methods = ['GET'])
def ultimasventas():
	if 'username' in session:
		dicindices = indices()
		with open('registros.csv') as archivo:
			archivo_csv = csv.reader(archivo)
			registro = next(archivo_csv)
			listaderegistros = []
			registro = next(archivo_csv)
			while registro:
				listaderegistros.append(registro)
				registro = next(archivo_csv, None)
		return render_template('ultimasventas.html', lista=listaderegistros, usuario=session['username'], indices=dicindices)
	else:
		return render_template('sin_permiso.html')

# Funcion para buscar los productos de un cliente determinado, buscando con 3 o mas caracteres
@app.route('/listarproductos', methods=['GET', 'POST'])
def listarproductos():
	if 'username' in session:
		formulario = ClienteForm()
		if formulario.validate_on_submit():
			cliente = formulario.cliente.data
			largocliente = len(cliente)
			if largocliente >= 3:
				return redirect(url_for('listadodeclientes',cliente=cliente, largo=largocliente))
			else:
				return render_template('listarproductos.html', form=formulario)	
	
		return render_template('listarproductos.html', form=formulario)
	else:
		return render_template('sin_permiso.html')

# Funcion que recibe los parametros de listarproductos y muestra las coincidencias y permite buscar un cliente determinado
@app.route('/listarproductosxclientes/<cliente>/<largo>', methods=['GET', 'POST'])
def listadodeclientes(cliente,largo):
	if 'username' in session:
		dicindices = indices()
		lista = listadodeclientesamostrar(largo,cliente)
		formulario = ClienteForm()
		if formulario.validate_on_submit():
			cliente = formulario.cliente.data
			with open('registros.csv') as archivo:
				archivo_csv = csv.reader(archivo)
				registro = next(archivo_csv)
				listadeproductos = []
				registro = next(archivo_csv)
				while registro:
					if cliente == registro[dicindices['indice_cliente']]:
						listadeproductos.append(registro)
					registro = next(archivo_csv, None)
			return render_template('listadeproductos.html', form=formulario, lista=listadeproductos,cliente=cliente, indices=dicindices)
		return render_template('listarproductosconopciones.html', form=formulario, lista=lista)	
	else:
		return render_template('sin_permiso.html')

# Funcion para buscar los clientes de un producto determinado, buscando con 3 o mas caracteres
@app.route('/listarclientes', methods=['GET', 'POST'])
def listarclientes():
	if 'username' in session:
		formulario = ProductoForm()
		if formulario.validate_on_submit():
			producto = formulario.producto.data
			largoproducto = len(producto)
			if largoproducto >= 3:
				return redirect(url_for('listadodeproductos',producto=producto, largo=largoproducto))
			else:
				return render_template('listarclientes.html', form=formulario)	
		return render_template('listarclientes.html', form=formulario)
	else:
		return render_template('sin_permiso.html')	

# Funcion que recibe los parametros de listarclientes y muestra las coincidencias y permite buscar un producto determinado
@app.route('/listarclientesxproducto/<producto>/<largo>', methods=['GET', 'POST'])
def listadodeproductos(producto,largo):
	if 'username' in session:
		dicindices = indices()
		lista = listadodeproductosamostrar(largo,producto)
		formulario = ProductoForm()
		if formulario.validate_on_submit():
			producto = formulario.producto.data
			with open('registros.csv') as archivo:
				archivo_csv = csv.reader(archivo)
				registro = next(archivo_csv)
				listadeclientes = []
				registro = next(archivo_csv)
				while registro:
					if producto == registro[dicindices['indice_producto']]:
						listadeclientes.append(registro)
					registro = next(archivo_csv, None)
			return render_template('listadeclientes.html', form=formulario, lista=listadeclientes,producto=producto, indices=dicindices)
		return render_template('listarclientesconopciones.html', form=formulario, lista=lista)
	else:
		return render_template('sin_permiso.html')		

# Funcion que muestra los productos mas vendidos
@app.route('/mas_vendidos', methods=['GET'])
def productosmasvendidos():
	if 'username' in session:
		dicindices = indices()
		with open('registros.csv') as archivo:
			archivo_csv = csv.reader(archivo)
			registro = next(archivo_csv)
			diccionariodeproductos = {}
			registro = next(archivo_csv)
			while registro:
				producto = registro[dicindices['indice_producto']]
				cantidad = registro[dicindices['indice_cantidad']]
				cantidad = int(cantidad)
				codigo = registro[dicindices['indice_codigo']]
				flag = diccionariodeproductos.get(producto)
				if flag == None:
					diccionariodeproductos[producto] = [cantidad, codigo]
				else:
					cantidad2 = diccionariodeproductos[producto]
					cantidad2 = int(cantidad2[0])
					diccionariodeproductos[producto] = [cantidad2 + cantidad, codigo]
				registro = next(archivo_csv, None)
		
			listaordenada = list(diccionariodeproductos.items())
			listaordenada.sort(key=lambda x: x[1], reverse=True)
			
		return render_template("masvendidos.html", lista=listaordenada)
	else:
		return render_template('sin_permiso.html')	

#Funcion que muestra los mejores clientes (los que mas gastaron)
@app.route('/mejores_clientes', methods=['GET'])
def mejoresclientes():
	if 'username' in session:
		with open('registros.csv') as archivo:
			dicindices = indices()
			archivo_csv = csv.reader(archivo)
			registro = next(archivo_csv)
			diccionariodeclientes = {}
			registro = next(archivo_csv)
			while registro:
				cliente = registro[dicindices['indice_cliente']]
				cantidad = registro[dicindices['indice_cantidad']]
				cantidad = int(cantidad)
				precio = registro[dicindices['indice_precio']]
				precio = float(precio)
				flag = diccionariodeclientes.get(cliente)

				if flag == None:
					diccionariodeclientes[cliente] = cantidad * precio
				else:
					cantidadbruta = diccionariodeclientes[cliente]
					total = cantidadbruta + (cantidad * precio)
					diccionariodeclientes[cliente] = round(total,2)

				registro = next(archivo_csv, None)		

			listaordenada = list(diccionariodeclientes.items())
			listaordenada.sort(key=lambda x: x[1], reverse=True)
			print(listaordenada)
			
		return render_template("mejoresclientes.html", lista=listaordenada)
	else:
		return render_template('sin_permiso.html')	

if __name__ == '__main__':
    app.run(debug = True)