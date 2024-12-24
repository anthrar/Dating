
/// Silver Wings 
function selectElement(id, valueToSelect) {
    let element = document.getElementById(id);
    element.value = valueToSelect;
}

function selectRadioElement(name, valueToSelect) {
    const radioButtons = document.querySelectorAll('input[name="' + name + '"]');
    for (const radioButton of radioButtons) {
        if (isNaN(valueToSelect)) {
            valueToSelect = '0'
        }
        if (radioButton.value === valueToSelect) {
            radioButton.checked = true;
            break;
        }
    }
}

function getFormData(form) {
    const formData = new FormData(form);
    const obj = {};
    formData.forEach(function(value, key){
        obj[key] = value;
    });
    return obj;
}
