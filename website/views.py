from flask import Blueprint, render_template, request, flash, jsonify
from flask_login import login_required, current_user
from .models import Note, Record
from . import db
import json

views = Blueprint('views', __name__)
@views.route('/', methods=['GET', 'POST'])
def home():
    return render_template("home.html", user=current_user)

@views.route('/optimization/', methods=['GET', 'POST'])
@login_required
def optimization():
    return render_template("optimization.html", user=current_user)

@views.route('/simulation/', methods=['GET', 'POST'])
@login_required
def simulation():
    if request.method == 'POST':
        import opyplus as op
        from numpy import genfromtxt
        from simulation_2 import simulation
        all_dir = "./BEM_files"
        idfname = '/545_update.idf'
        epwfile = "/Austin_weather.epw"
        eplus = '/my_simulation'
        epm = op.Epm().load(all_dir  + idfname)
        y = genfromtxt(all_dir + "/ActualEnergyConsumption.csv", delimiter=',')
        S = simulation(epm, all_dir + epwfile, all_dir + eplus)

        solar_transmittance = request.form.get('solar_transmittance')
        lighting_level = request.form.get('lighting_level')
        burner_efficiency = request.form.get('burner_efficiency')
        maximum_supply_air_temperature = request.form.get('maximum_supply_air_temperature')
        fan_total_efficiency = request.form.get('fan_total_efficiency')

        if solar_transmittance: solar_transmittance = float(solar_transmittance)
        if lighting_level: lighting_level = float(lighting_level)
        if burner_efficiency: burner_efficiency = float(burner_efficiency)
        if maximum_supply_air_temperature: maximum_supply_air_temperature = float(maximum_supply_air_temperature)
        if fan_total_efficiency: fan_total_efficiency = float(fan_total_efficiency)

        if solar_transmittance:
            if solar_transmittance > 0.001 and solar_transmittance < 0.999:
                w = S.epm.WindowMaterial_Shade.one(lambda x: x.name == "coolingshade")
                w.solar_transmittance = solar_transmittance
                w.solar_reflectance = 0.999 - solar_transmittance
            else:
                flash("solar transmittance is beyond its bound", category="error")
                return render_template("simulation.html", user=current_user)

        if lighting_level:
            if lighting_level > 300 and lighting_level < 700:
                w = S.epm.Lights.one(lambda x: x.name == "living hw & plugin lighting_1")
                w.lighting_level = lighting_level
            else:
                flash("lighting level is beyond its bound", category="error")
                return render_template("simulation.html", user=current_user)

        if burner_efficiency:
            if burner_efficiency > 0.5 and burner_efficiency < 0.999:
                w = S.epm.Coil_Heating_Fuel.one(lambda x:x.name == "furnace heating coil_1")
                w.burner_efficiency = burner_efficiency
            else:
                flash("burner efficiency is beyond its bound", category="error")
                return render_template("simulation.html", user=current_user)

        if maximum_supply_air_temperature:
            if maximum_supply_air_temperature > 30 and maximum_supply_air_temperature < 70:
                w = S.epm.AirLoopHVAC_UnitaryHeatCool.one(lambda x:x.name == "forced air system_1")
                w.maximum_supply_air_temperature = maximum_supply_air_temperature
            else:
                flash("maximum supply air temperature", category="error")
                return render_template("simulation.html", user=current_user)

        if fan_total_efficiency:
            if fan_total_efficiency > 0.001 and fan_total_efficiency < 0.999:
                w = S.epm.Fan_onOff.one(lambda x: x.name == "supply fan_1")
                w.fan_total_efficiency = fan_total_efficiency
            else:
                flash("fan total efficiency is beyond its bound", category="error")
                return render_template("simulation.html", user=current_user)

        status, yc = S.simulate()
        if status:
            res = S.MSE(y, yc)
            new_record = Record(data=res, user_id=current_user.id)
            db.session.add(new_record)
            db.session.commit()
            flash('Simulation completed!', category='success')
        else:
            flash('Simulation failed!', category='error')

    return render_template('simulation.html', user=current_user)

@views.route('/delete-note', methods=['POST'])
@login_required
def delete_note():
    note = json.loads(request.data)
    noteId = note['noteId']
    note = Note.query.get(noteId)
    if note:
        if note.user_id == current_user.id:
            db.session.delete(note)
            db.session.commit()

    return jsonify({})

@views.route('/delete-record', methods=['POST'])
@login_required
def delete_record():
    record = json.loads(request.data)
    recordId = record['recordId']
    record = Record.query.get(recordId)
    if record:
        if record.user_id == current_user.id:
            db.session.delete(record)
            db.session.commit()

    return jsonify({})
