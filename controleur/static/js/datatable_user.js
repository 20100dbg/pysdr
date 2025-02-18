
let start_daterange;
let end_daterange;
let table_obj;
let picker;


//module / gdh / frq / pwr
const data = {"headings": ["Module", "Gdh", "FRQ", "PWR"],
    "data": [
        ["1", "2025-02-17 20:12:00", "400.500", "-15"],
        ["2", "2025-02-17 20:35:00", "410.250", "-7"],
        ["1", "2025-02-17 20:42:00", "405.800", "-10"],
        ["3", "2025-02-17 20:59:00", "412.100", "-18"],
        ["1", "2025-02-17 21:05:00", "405.500", "-16"],
        ["2", "2025-02-17 21:17:00", "407.500", "-22"],
        ["1", "2025-02-17 21:22:00", "402.350", "-30"],
    ]};



window.onload = (event) => {
    table_obj = new simpleDatatables.DataTable("#myTable", {
        type: "string",
        paging: false,
        searchable: true,

        columns: [
            {select: 1, type: "date",format: "MYSQL",
              searchMethod: (terms, cell, row, _column, source) => {
                if (source === "date-filter") {
                    let start = parseInt(terms[0]);
                    let end = parseInt(terms[1]);

                    return (start <= cell.order && cell.order <= end);
                }
            }
            },
            {select: 2, 
                searchMethod: (terms, cell, row, _column, source) => {
                    let mycell = parseFloat(cell.data);
                    let min = parseFloat(terms[0]);

                    if (terms.length == 2)
                        return (mycell >= min && mycell <= parseFloat(terms[1]) +1);

                    return (mycell > min -1 && mycell < min + 1);
                }
            },
            {select: 3,                 
                searchMethod: (terms, cell, row, _column, source) => {
                    mycell = parseInt(cell.data);
                    if (terms.length == 2)
                        return (mycell >= parseInt(terms[0]) && mycell <= parseInt(terms[1]) ||
                                    mycell <= parseInt(terms[0]) && mycell >= parseInt(terms[1]));
                    return (mycell == parseInt(terms[0]));
                }}
        ],

        tableRender: (_data, table, type) => {

            const tHead = table.childNodes[0];
            const filterHeaders = {
                nodeName: "TR",
                childNodes: tHead.childNodes[0].childNodes.map(
                    (_th, index) => ({nodeName: "TH",
                        childNodes: [{
                                nodeName: "INPUT",
                                attributes: {
                                    class: "datatable-input",
                                    type: "search",
                                    "data-columns": `[${index}]`
                                }
                            }
                        ]})
                )
            }

            //remove filter for datetime column
            filterHeaders.childNodes[1] = {nodeName: "TH",childNodes: [{nodeName: "INPUT", attributes: {id: "datepicker"}}]};

            tHead.childNodes.push(filterHeaders)
            return table
        },

        data
    });

    document.getElementsByClassName("datatable-search")[0].remove();


    picker = new easepick.create({
        element: document.getElementById('datepicker'),
        css: ['easypick.css'], //'https://cdn.jsdelivr.net/npm/@easepick/bundle@1.2.1/dist/index.css',
        autoApply: false,
        resetButton: true,
        plugins: ['RangePlugin', 'TimePlugin'],
        TimePlugin: {format: 'HH:mm'},
        RangePlugin: { tooltipNumber(num) { return num - 1; } },

        setup(picker) {
          picker.on('select', (e) => {
            start_daterange = e.detail.start;
            end_daterange = e.detail.end;
            //start_daterange, end_daterange
            table_obj.multiSearch([{terms: [""+(start_daterange.getTime()/1000), ""+(end_daterange.getTime()/1000)], columns: [1]}], "date-filter")
          });
        },
    });

    let dom_datepicker = document.getElementById("datepicker");
    const tpl = document.createElement('template');
    tpl.innerHTML = '<button onclick="cancel_datepicker();">X</button>';
    dom_datepicker.parentNode.appendChild(tpl.content.firstChild);




};


function cancel_datepicker() {
    picker.clear();
    table_obj.refresh();
}

function get_search_results() {
    tab_row_idx = table_obj._searchData;
    console.log(tab_row_idx);
}


function importdata(module_id, dt, frq, pwr) {
    let newData = {"cells": [{"data": module_id},{"data": dt},{"data": frq},{"data": pwr}]};
    table_obj.data.data = table_obj.data.data.concat(newData)
    table_obj.update();
}