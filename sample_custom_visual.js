const { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } = Recharts;
const { createElement } = React;

module.exports = {
    id: "com.example.areachart",
    name: "Gradient Area Chart",
    icon: "",
    configSchema: {
        dataKey: { type: "string", default: "value" },
        xAxisKey: { type: "string", default: "name" }
    },
    render: function(props) {
        const { data, config } = props;
        const dataKey = config?.dataKey || "value";
        const xAxisKey = config?.xAxisKey || "name";

        return createElement(ResponsiveContainer, { width: "100%", height: "100%" },
            createElement(AreaChart, { data: data, margin: { top: 10, right: 30, left: 0, bottom: 0 } },
                createElement("defs", null,
                    createElement("linearGradient", { id: "colorValue", x1: "0", y1: "0", x2: "0", y2: "1" },
                        createElement("stop", { offset: "5%", stopColor: "#8884d8", stopOpacity: 0.8 }),
                        createElement("stop", { offset: "95%", stopColor: "#8884d8", stopOpacity: 0 })
                    )
                ),
                createElement(XAxis, { dataKey: xAxisKey }),
                createElement(YAxis),
                createElement(CartesianGrid, { strokeDasharray: "3 3" }),
                createElement(Tooltip),
                createElement(Area, { 
                    type: "monotone", 
                    dataKey: dataKey, 
                    stroke: "#8884d8", 
                    fillOpacity: 1, 
                    fill: "url(#colorValue)" 
                })
            )
        );
    }
};
