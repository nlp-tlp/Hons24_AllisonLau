# Path queries
PO_MATCH =  """
                OPTIONAL MATCH (connect_objects:PhysicalObject)-[:hasPart|contains*1..]->(o)
                OPTIONAL MATCH (o)-[:isA*]->(substitute_objects:PhysicalObject)
            """
PO_RETURN = """
                collect(properties(connect_objects)) AS connect_objects, 
                collect(properties(substitute_objects)) AS substitute_objects
            """

PP_MATCH =  "OPTIONAL MATCH (p)-[:isA*]->(substitute_property:Property)"
PP_RETURN = "collect(properties(substitute_property)) AS substitute_property"

PC_MATCH =  "OPTIONAL MATCH (p)-[:isA*]->(substitute_process:Process)"
PC_RETURN = "collect(properties(substitute_process)) AS substitute_process"

ST_MATCH =  "OPTIONAL MATCH (s)-[:isA*]->(substitute_state:State)"
ST_RETURN = "collect(properties(substitute_state)) AS substitute_state"

AT_MATCH =  "OPTIONAL MATCH (a)-[:isA*]->(substitute_activity:Activity)"
AT_RETURN = "collect(properties(substitute_activity)) AS substitute_activity"

direct_queries = [
    { # Query 1: Find all OBJECT with undesirable properties
        "query": f"""MATCH (o:PhysicalObject)-[:hasProperty]->(p:Property {{subtype0: "UndesirableProperty"}})
                    {PO_MATCH} {PP_MATCH}
                    RETURN properties(o) AS object_properties, properties(p) AS property_properties,
                    {PO_RETURN}, {PP_RETURN}
                """,
        "outfile": "object_property_paths",
        "event": "property",
        "relation": "hasProperty"
    },
    { # Query 2: Find all undesirable processes with AGENTS OBJECT
        "query": f"""
                    MATCH (p:Process {{subtype0: 'UndesirableProcess'}})-[:hasParticipant_hasAgent]->(o:PhysicalObject)
                    {PO_MATCH} {PC_MATCH}
                    RETURN properties(o) AS object_properties, properties(p) AS process_properties,
                    {PO_RETURN}, {PC_RETURN}
                """,
        "outfile": "process_agent_paths",
        "event": "process",
        "relation": "hasAgent"
    },
    { # Query 3: Find all undesirable processes with PATIENTS OBJECT
        "query": f"""
                    MATCH (p:Process {{subtype0: 'UndesirableProcess'}})-[:hasParticipant_hasPatient]->(o:PhysicalObject)
                    {PO_MATCH} {PC_MATCH}
                    RETURN properties(o) AS object_properties, properties(p) AS process_properties,
                    {PO_RETURN}, {PC_RETURN}
                """,
        "outfile": "process_patient_paths",
        "event": "process",
        "relation": "hasPatient"
    },
    { # Query 4: Find all undesirable states with PATIENTS OBJECT
        "query": f"""
                    MATCH (s:State {{subtype0: 'UndesirableState'}})-[:hasParticipant_hasPatient]->(o:PhysicalObject)
                    {PO_MATCH} {ST_MATCH}
                    RETURN properties(o) AS object_properties, properties(s) AS state_properties,
                    {PO_RETURN}, {ST_RETURN}
                """,
        "outfile": "state_patient_paths",
        "event": "state",
        "relation": "hasPatient"
    }
]

complex_queries = [
    { # Query 5: Find all OBJECT with PROPERTIES linked to undesirable states
        "query": f"""
                    MATCH (o:PhysicalObject)-[:hasProperty]->(p:Property)
                    MATCH (s:State {{subtype0: 'UndesirableState'}})-[:hasParticipant_hasPatient]->(p)
                    {PO_MATCH} {PP_MATCH} {ST_MATCH}
                    RETURN properties(o) AS object_properties, properties(p) AS property_properties, properties(s) AS state_properties,
                    {PO_RETURN}, {PP_RETURN}, {ST_RETURN}
                """,
        "outfile": "object_property_state_paths",
        "event": "property",
        "helper": "state",
        "relation": "hasProperty"
    },
    { # Query 6: Find all OBJECT with PROCESSES linked to undesirable states
        "query": f"""
                    MATCH (o:PhysicalObject)-[:hasParticipant_hasPatient]->(p:Process)
                    MATCH (s:State {{subtype0: 'UndesirableState'}})-[:hasParticipant_hasPatient]->(p)
                    {PO_MATCH} {PC_MATCH} {ST_MATCH}
                    RETURN properties(o) AS object_properties, properties(p) AS process_properties, properties(s) AS state_properties,
                    {PO_RETURN}, {PC_RETURN}, {ST_RETURN}
                """,
        "outfile": "object_process_state_paths",
        "event": "process",
        "helper": "state",
        "relation": "hasPatient"
    },
    { # Query 7: Find all undesirable states with agents OBJECT where states linked to activities
        "query": f"""
                    MATCH (s:State {{subtype0: 'UndesirableState'}})-[:hasParticipant_hasAgent]->(o:PhysicalObject)
                    MATCH (s)-[:hasParticipant_hasPatient]->(a:Activity) 
                    {PO_MATCH} {ST_MATCH} {AT_MATCH}
                    RETURN properties(o) AS object_properties, properties(s) AS state_properties, properties(a) AS activity_properties, 
                    {PO_RETURN}, {ST_RETURN}, {AT_RETURN}
                """,
        "outfile": "state_agent_activity_paths",
        "event": "state",
        "helper": "activity",
        "relation": "hasAgent"
    },
    { # Query 8: Find all undesirable states with agents OBJECT where states have patient OBJECT
        "query": f"""
                    MATCH (s:State {{subtype0: 'UndesirableState'}})-[:hasParticipant_hasAgent]->(o:PhysicalObject)
                    MATCH (s)-[:hasParticipant_hasPatient]->(o2:PhysicalObject) 
                    {PO_MATCH} {ST_MATCH} 
                    RETURN properties(o) AS object_properties, properties(s) AS state_properties, properties(o2) AS patient_properties, 
                    {PO_RETURN}, {ST_RETURN}
                """,
        "outfile": "state_agent_patient_paths",
        "event": "state",
        "helper": "patient",
        "relation": "hasAgent"
    },
    { # Query 9: Find all undesirable processes with agents OBJECT where processes have patient OBJECT
        "query": f"""
                    MATCH (p:Process {{subtype0: 'UndesirableProcess'}})-[:hasParticipant_hasAgent]->(o:PhysicalObject)
                    MATCH (p)-[:hasParticipant_hasPatient]->(o2:PhysicalObject) 
                    {PO_MATCH} {PC_MATCH}
                    RETURN properties(o) AS object_properties, properties(p) AS process_properties, properties(o2) AS patient_properties, 
                    {PO_RETURN}, {PC_RETURN}
                """,
        "outfile": "process_agent_patient_paths",
        "event": "process",
        "helper": "patient",
        "relation": "hasAgent"
    }
]

