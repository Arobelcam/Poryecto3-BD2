from neo4j import GraphDatabase

#configuracion de neo4j
URI = "neo4j+ssc://551c5c73.databases.neo4j.io"
USERNAME = "neo4j"
PASSWORD = "Zltdp3raSar5tXbF8TjmGr15Jv3onamt6uO5TjR_oXU"

driver = GraphDatabase.driver(URI, auth=(USERNAME, PASSWORD))


def cerrar_conexion():
    driver.close()

def pieza_presente(pieza_id):
    query = """
    MATCH (p:Pieza {PiezaID:$id, Estado:true})
    RETURN p LIMIT 1
    """
    with driver.session(database="neo4j") as s:
        return s.run(query, id=pieza_id).single() is not None

#funciones para obtener piezas y bordes
def obtener_piezas_validas(rompecabezas_id):
    query = """
    MATCH (r:Rompecabezas {RompecabezasID:$rid})-[:Compuesto_por]->(p:Pieza)
    WHERE p.Estado = true
    RETURN p.PiezaID AS id, p.BordeCompartido AS compartido
    """
    with driver.session(database="neo4j") as s:
        result = s.run(query, rid=rompecabezas_id)
        return [{"id": r["id"], "compartido": r["compartido"]} for r in result]

def obtener_bordes_salida_validos(pieza_id):
    query = """
    MATCH (p:Pieza {PiezaID:$pid, Estado:true})-[:Tiene]->(b:Borde)
    WHERE b.EntradaOSalida = 0 AND b.Compartido = 0
    RETURN b.BordeID AS id
    """
    with driver.session(database="neo4j") as s:
        result = s.run(query, pid=pieza_id)
        return [r["id"] for r in result]

def obtener_bordes_validos(pieza_id):
    query = """
    MATCH (p:Pieza {PiezaID:$pid, Estado:true})-[:Tiene]->(b:Borde)
    WHERE b.Compartido = 0
    RETURN b.BordeID AS id
    """
    with driver.session(database="neo4j") as s:
        result = s.run(query, pid=pieza_id)
        return [r["id"] for r in result]

def obtener_conexion_de_borde(borde_id):
    query = """
    MATCH (b1:Borde {BordeID:$bid})-[:Conecta_en]-(b2:Borde)<-[:Tiene]-(p:Pieza)
    WHERE p.Estado = true
    RETURN b2.BordeID AS borde_entrada, p.PiezaID AS pieza_destino
    """
    with driver.session(database="neo4j") as s:
        result = s.run(query, bid=borde_id)
        return [{"borde_entrada": r["borde_entrada"],
                 "pieza_destino": r["pieza_destino"]} for r in result]

# ───────── Algoritmo para armar el rompecabezas ─────────
def resolver_rompecabezas(rompecabezas_id, pieza_inicial=None):
    """
    Recorre todas las piezas presentes (Estado=true) del rompecabezas,
    empezando por `pieza_inicial` si está disponible; si no, la omite
    y continúa con el resto.
    """
    # lista de IDs de piezas presentes
    piezas_validas = [p["id"] for p in obtener_piezas_validas(rompecabezas_id)]
    if not piezas_validas:
        return ["No hay piezas disponibles."]

    # semillas para el DFS: pieza_inicial (si existe) + el resto
    semillas = []
    if pieza_inicial and pieza_inicial in piezas_validas:
        semillas.append(pieza_inicial)
    semillas += [pid for pid in piezas_validas if pid not in semillas]

    visitadas          = set()
    conexiones_usadas  = set()
    instrucciones      = []

    for seed in semillas:
        if seed in visitadas:
            continue
        pila = [seed]

        while pila:
            pieza_actual = pila.pop()
            if pieza_actual in visitadas:
                continue
            visitadas.add(pieza_actual)

            # bordes válidos de la pieza actual
            for borde in obtener_bordes_validos(pieza_actual):
                for conexion in obtener_conexion_de_borde(borde):
                    pieza_destino   = conexion["pieza_destino"]
                    borde_conectado = conexion["borde_entrada"]

                    # evita duplicar la misma unión (orden irrelevante)
                    clave = tuple(sorted([borde, borde_conectado]))
                    if clave in conexiones_usadas:
                        continue
                    conexiones_usadas.add(clave)

                    instrucciones.append(
                        f"Conectar borde {borde} de pieza {pieza_actual} "
                        f"con borde {borde_conectado} de pieza {pieza_destino}"
                    )

                    if pieza_destino not in visitadas:
                        pila.append(pieza_destino)

    return instrucciones

# ───────── Ejecución principal ─────────
if __name__ == "__main__":
    rompecabezas_id = "caracol2"
    pieza_inicial   = "c5"           # se salta si está perdida

    print("\nPiezas válidas en el rompecabezas:")
    for p in obtener_piezas_validas(rompecabezas_id):
        print(p)

    print(f"\nBordes de salida válidos de la pieza {pieza_inicial}:")
    print(obtener_bordes_salida_validos(pieza_inicial))

    print("\nInstrucciones para armar el rompecabezas:")
    for paso in resolver_rompecabezas(rompecabezas_id, pieza_inicial):
        print(paso)

    cerrar_conexion()
