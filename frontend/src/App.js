import React from 'react';
import axios from "axios";
import './App.css';

import OrderList from "./components/Orders";


class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            'orders': [],
        }
    }

    componentDidMount() {
        const headers = {
            'Content-Type': 'application/json'
        }

        axios.get('http://127.0.0.1:8000/api/orders/', {headers}).then(response => {
                this.setState(
                    {
                        "orders": response.data
                    }
                )
            }
        ).catch(error => console.log(error))
    }

    render() {
        return (
            <div>
                <OrderList orders={this.state.orders}/>
            </div>
        );
    }
}

export default App;