from neo4j import GraphDatabase

# Configuración de conexión
URI = "neo4j+s://551c5c73.databases.neo4j.io"
USERNAME = "neo4j"
PASSWORD = "Zltdp3raSar5tXbF8TjmGr15Jv3onamt6uO5TjR_oXU"

# Crear driver
driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))

def cerrar_conexion():
    driver.close()

def obtener_piezas_validas(rompecabezas_id):
    """
    Devuelve una lista de piezas del rompecabezas que no están marcadas como perdidas (Estado = True).
    """
    query = """
    MATCH (r:Rompecabezas {RompecabezasID: $rompecabezas_id})-[:Compuesto_por]->(p:Pieza)
    WHERE p.Estado = true
    RETURN p.PiezaID AS id, p.BordeCompartido AS compartido
    """
    with driver.session(database="neo4j") as session:
        result = session.run(query, rompecabezas_id=rompecabezas_id)
        piezas = [{"id": r["id"], "compartido": r["compartido"]} for r in result]
    return piezas

def obtener_bordes_salida_validos(pieza_id):
    """
    Devuelve los bordes de salida (EntradaOSalida = 0) de una pieza, excluyendo los compartidos.
    """
    query = """
    MATCH (p:Pieza {PiezaID: $pieza_id})-[:Tiene]->(b:Borde)
    WHERE b.EntradaOSalida = 0 AND b.Compartido = 0
    RETURN b.BordeID AS id
    """
    with driver.session(database="neo4j") as session:
        result = session.run(query, pieza_id=pieza_id)
        return [r["id"] for r in result]

def obtener_conexion_de_borde(borde_id):
    """
    Dado un borde de salida, devuelve el borde de entrada al que se conecta y la pieza a la que pertenece.
    """
    query = """
    MATCH (b1:Borde {BordeID: $borde_id})-[:Conecta_en]->(b2:Borde)<-[:Tiene]-(p:Pieza)
    RETURN b2.BordeID AS borde_entrada, p.PiezaID AS pieza_destino
    """
    with driver.session(database="neo4j") as session:
        result = session.run(query, borde_id=borde_id)
        return [{"borde_entrada": r["borde_entrada"], "pieza_destino": r["pieza_destino"]} for r in result]

def resolver_rompecabezas(pieza_inicial):
    """
    Algoritmo DFS para recorrer las piezas conectadas, evitando ciclos y bordes compartidos.
    """
    piezas_colocadas = set()
    instrucciones = []
    pila = [pieza_inicial]

    while pila:
        pieza_actual = pila.pop()
        if pieza_actual in piezas_colocadas:
            continue
        piezas_colocadas.add(pieza_actual)

        bordes = obtener_bordes_salida_validos(pieza_actual)

        for borde_salida in bordes:
            conexiones = obtener_conexion_de_borde(borde_salida)

            for conexion in conexiones:
                pieza_destino = conexion["pieza_destino"]
                borde_entrada = conexion["borde_entrada"]

                if pieza_destino not in piezas_colocadas:
                    instrucciones.append(
                        f"Conectar borde {borde_salida} de pieza {pieza_actual} "
                        f"con borde {borde_entrada} de pieza {pieza_destino}"
                    )
                    pila.append(pieza_destino)

    return instrucciones

# ---------- EJECUCIÓN PRINCIPAL ----------
if __name__ == "__main__":
    rompecabezas_id = "tiburon1"   # <- Cambia este ID si es diferente en tu base
    pieza_inicial = "ti2"    # <- Cambia esta pieza por la inicial deseada

    print(" Piezas válidas en el rompecabezas:")
    piezas_validas = obtener_piezas_validas(rompecabezas_id)
    for p in piezas_validas:
        print(p)

    print(f"\n Bordes de salida válidos de la pieza {pieza_inicial}:")
    bordes_salida = obtener_bordes_salida_validos(pieza_inicial)
    print(bordes_salida)

    print("\n Conexiones posibles desde esos bordes:")
    for borde in bordes_salida:
        conexiones = obtener_conexion_de_borde(borde)
        if conexiones:
            for c in conexiones:
                print(f"Borde {borde} se conecta con el borde {c['borde_entrada']} de la pieza {c['pieza_destino']}")
        else:
            print(f"Borde {borde} no tiene conexiones.")

    print("\n Instrucciones para armar el rompecabezas:")
    instrucciones = resolver_rompecabezas(pieza_inicial)
    for paso in instrucciones:
        print(paso)

    cerrar_conexion()
