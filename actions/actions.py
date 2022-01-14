# https://rasa.com/docs/rasa/custom-actions
import mysql.connector
from typing import Any, Text, Dict, List
from bson import json_util
import json

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

#connect rasa to db
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="przychodnia"
)
conn = mydb.cursor()

#we assume that user is logged and have some Id to authenticate him
userId = 6

#method to find last visit as a user
class ActionSearchLastUserVisit(Action):

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_search_last_user_visit"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        sql = "SELECT * FROM VISIT v WHERE v.patient_id_ID = %s LIMIT 0, 1"
        val = (userId,)

        conn.execute(sql, val)

        result = conn.fetchall()

        date = json.dumps(result[0][1], indent=4, sort_keys=True, default=str)
        time = json.dumps(result[0][5], indent=4, sort_keys=True, default=str)
        response = "your last visit was: "+date+" "+time
        dispatcher.utter_message(text=response)

        return []

#method to find when patient(person)  had last visit (as a doctor)
class ActionSearchLastPatientVisit(Action):

    def name(self) -> Text:
        """Unique identifier of the action"""
        return "action_doctor_search_last_user_visit"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        slots = {
            "person" : ""
        }
        print(domain)
        print(tracker.get_latest_entity_values('person'))
        print(tracker.get_slot('person'))
        tracker.current_slot_values()

        patientName, patientSurname = tracker.get_slot('person').split(sep=" ")

        # check if user has sufficient role to get information
        testPermission = "SELECT r.name FROM USER_ROLES u LEFT JOIN ROLE r on r.role_id = u.roles_role_id WHERE %s"
        val = (userId,)
        conn.execute(testPermission, val)
        permissionsLevel = conn.fetchall()[0][0]
        print(permissionsLevel)
        if (not permissionsLevel == "DOCTOR" and not permissionsLevel == "ADMIN"):
           response = "You don't have enough permissions to get this information!"
           dispatcher.utter_message(text=response)
           return []

        # get ID of requested user from database
        userIdSQL = "SELECT u.id FROM USER u WHERE u.first_name = %s AND u.second_name = %s limit 0, 1"
        val = (patientName, patientSurname,)
        conn.execute(userIdSQL, val)
        userID = conn.fetchone()

        if userID == None:
           response = "Patient doesn't exist!"
           dispatcher.utter_message(text=response)
           return []

        # get user data based on ID fetched above and check if requested patient attended
        sql = "SELECT * FROM VISIT v WHERE v.patient_id_ID = %s LIMIT 0, 1"
        val = (userID[0],)
        conn.execute(sql, val)
        result = conn.fetchall()
        if result == []:
           response = "Patient doesn't attend!"
           dispatcher.utter_message(text=response)
           return []

        #print(result)

        # print tabulated data to requester
        date = json.dumps(result[0][1], indent=4, sort_keys=True, default=str)
        time = json.dumps(result[0][5], indent=4, sort_keys=True, default=str)
        response = patientName + " " + patientSurname + " last visit was: " + date + " " + time
        dispatcher.utter_message(text=response)

        return []

