let datatable_obj;
let datatable_picker;
let datatable_css = '../static/css/easypick.css';
//'https://cdn.jsdelivr.net/npm/@easepick/bundle@1.2.1/dist/index.css',

function datatable_init() {

    const data = {"headings": ["ID", "GDH", "FRQ", "PWR"], "data": []};

    datatable_obj = new simpleDatatables.DataTable("#myTable", {
        type: "string",
        //scrollY: "1000px",
        //hiddenHeader: true,
        paging: true,
        searchable: true,

        //handle custom search in columns
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

        rowRender: (rowValue, tr, index) => {
            tr.attributes["class"] = (index % 2 == 0) ? "row-even" : "row-odd";
            return tr;
        },

        //show custom search textbox in columns
        tableRender: (_data, table, type) => {

            const placeholders = ["ID MODULE", "", "408.5 ou 400 410", "-3 ou -5 -10" ]
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
                                    "data-columns": `[${index}]`,
                                    id: "search-" + `${index}`,
                                    style: "width:50%",
                                    placeholder: placeholders[`${index}`]
                                }
                            }
                        ]})
                )
            }

            //remove textbox for datetime column
            filterHeaders.childNodes[1] = {nodeName: "TH",childNodes: [{nodeName: "INPUT", attributes: {id: "datepicker", style: "width: 50%"}}]};

            tHead.childNodes.push(filterHeaders)
            return table
        },

        //data to import
        data
    });

    //remove global search textbox
    document.getElementsByClassName("datatable-search")[0].remove();


    //init datetime picker
    datatable_picker = new easepick.create({
        element: document.getElementById('datepicker'),
        css: [datatable_css],
        autoApply: false,
        resetButton: true,
        plugins: ['RangePlugin', 'TimePlugin'],
        TimePlugin: {format: 'HH:mm'},
        RangePlugin: { tooltipNumber(num) { return num - 1; } },

        setup(picker) {
          picker.on('select', (e) => {
            datatable_obj.multiSearch([{terms: [""+(e.detail.start.getTime()/1000), 
                                            ""+(e.detail.end.getTime()/1000)], 
                                            columns: [1]}], "date-filter")
          });
        },
    });


    //Insert datetime picker into DOM
    let dom_datepicker = document.getElementById("datepicker");
    const tpl = document.createElement('template');
    tpl.innerHTML = '<button onclick="cancel_datepicker();">X</button>';
    dom_datepicker.parentNode.appendChild(tpl.content.firstChild);
}


function cancel_datepicker() {
    datatable_picker.clear();
    datatable_obj.refresh();
}

//Returns row index from search results
function get_search_results() {
    tab_row_idx = datatable_obj._searchData;

    //toutes les données
    if (is_undefined(tab_row_idx)) {
        draw_heatmap(detections);
    }
    else {
        let data = [];
        for (let i = 0; i < tab_row_idx.length; i++) {
            let idx_row = tab_row_idx[i];
            data.push(detections[idx_row]);
        }
        draw_heatmap(data);
    }
}


function remove_filters() {
    
    document.getElementById("search-0").innerText = "";
    datatable_picker.clear();
    document.getElementById("search-2").innerText = "";
    document.getElementById("search-3").innerText = "";

    datatable_obj.refresh();
}

function empty_table() {
    //let all_indexes = [0,1,2,3];
    //datatable_obj.rows.remove(all_indexes);
    
    let nb_rows = datatable_obj.data.data.length ;
    for (var i = 0; i < nb_rows; i++) {
        datatable_obj.rows.remove(i);
    }
}

//import block of data
function datatable_import(data) {

    datatable_obj.insert({"data": data});

    datatable_obj.update();
    datatable_obj.refresh();
}