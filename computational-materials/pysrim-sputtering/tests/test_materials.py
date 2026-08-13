"""
Tests for material definitions and database.
"""
import pytest
from src.utils.config_loader import load_materials, MaterialConfig
from src.materials.database import MaterialDatabase
from src.materials.definitions import (
    make_sio2_layer, make_tio2_layer, make_ito_layer,
    make_multilayer_target, make_target,
)


class TestConfigLoader:
    def test_load_materials(self, materials_config_path):
        materials = load_materials(materials_config_path)
        assert 'SiO2' in materials
        assert 'TiO2' in materials
        assert 'ITO' in materials

    def test_sio2_properties(self, materials_config_path):
        materials = load_materials(materials_config_path)
        sio2 = materials['SiO2']
        assert sio2.density == pytest.approx(2.20)
        assert 'Si' in sio2.elements
        assert 'O' in sio2.elements
        assert sio2.elements['Si'].stoich == pytest.approx(1.0)
        assert sio2.elements['O'].stoich == pytest.approx(2.0)

    def test_tio2_properties(self, materials_config_path):
        materials = load_materials(materials_config_path)
        tio2 = materials['TiO2']
        assert tio2.density == pytest.approx(4.23)
        assert 'Ti' in tio2.elements
        assert tio2.elements['Ti'].stoich == pytest.approx(1.0)
        assert tio2.elements['O'].stoich == pytest.approx(2.0)

    def test_ito_composition(self, materials_config_path):
        materials = load_materials(materials_config_path)
        ito = materials['ITO']
        assert 'In' in ito.elements
        assert 'Sn' in ito.elements
        assert 'O' in ito.elements
        assert ito.elements['In'].stoich == pytest.approx(1.8)
        assert ito.elements['Sn'].stoich == pytest.approx(0.2)
        assert ito.elements['O'].stoich == pytest.approx(3.0)

    def test_density_range(self, materials_config_path):
        materials = load_materials(materials_config_path)
        for name, mat in materials.items():
            assert 0.1 < mat.density < 25.0, f"{name} density out of range"

    def test_displacement_energies_positive(self, materials_config_path):
        materials = load_materials(materials_config_path)
        for name, mat in materials.items():
            for sym, elem in mat.elements.items():
                assert elem.E_d > 0, f"{name}/{sym} E_d must be positive"
                assert elem.surface >= 0, f"{name}/{sym} surface binding must be non-negative"


class TestMaterialDatabase:
    def test_list_materials(self):
        db = MaterialDatabase()
        names = db.list_materials()
        assert len(names) >= 3
        assert 'SiO2' in names

    def test_get_density(self):
        db = MaterialDatabase()
        assert db.get_density('SiO2') == pytest.approx(2.20)
        assert db.get_density('TiO2') == pytest.approx(4.23)
        assert db.get_density('ITO') == pytest.approx(7.10)

    def test_get_layer(self):
        db = MaterialDatabase()
        layer = db.get_layer('SiO2')
        assert layer.density == pytest.approx(2.20)
        assert layer.width == 50000

    def test_get_layer_width_override(self):
        db = MaterialDatabase()
        layer = db.get_layer('TiO2', width_override=5000)
        assert layer.width == 5000

    def test_unknown_material_raises(self):
        db = MaterialDatabase()
        with pytest.raises(KeyError):
            db.get_material('Unknown')

    def test_composition_string(self):
        db = MaterialDatabase()
        comp = db.get_composition_string('SiO2')
        assert 'Si' in comp
        assert 'O' in comp

    def test_summary(self):
        db = MaterialDatabase()
        summary = db.summary()
        assert 'SiO2' in summary
        assert 'TiO2' in summary


class TestDefinitions:
    def test_make_sio2_layer(self):
        layer = make_sio2_layer()
        assert layer.density == pytest.approx(2.20)
        assert layer.width == 50000

    def test_make_tio2_layer(self):
        layer = make_tio2_layer()
        assert layer.density == pytest.approx(4.23)
        assert layer.width == 600

    def test_make_tio2_custom_density(self):
        layer = make_tio2_layer(density=4.0)
        assert layer.density == pytest.approx(4.0)

    def test_make_ito_layer(self):
        layer = make_ito_layer()
        assert layer.density == pytest.approx(7.10)
        assert layer.width == 1500

    def test_make_multilayer_target(self):
        target = make_multilayer_target(tio2_width_angstrom=600)
        assert len(target.layers) == 2
        assert target.layers[0].width == 600     # TiO2 optical coating
        assert target.layers[1].width == 1500    # ITO conductor

    def test_make_target_by_name(self):
        target = make_target("SiO2")
        assert len(target.layers) == 1
        assert target.layers[0].density == pytest.approx(2.20)

    def test_make_target_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown material"):
            make_target("NonExistent")
