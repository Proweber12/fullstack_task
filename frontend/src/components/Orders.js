import React from "react";

const OrderItem = ({order}) => {
    return (
        <tr>

            <td className='cell'>{order.id}</td>

            <td className='cell'>{order.order_number}</td>

            <td className='cell'>{order.price_usd}</td>

            <td className='cell'>{order.delivery_time}</td>

            <td className='cell'>{order.price_rub}</td>

        </tr>
    )
}

const OrderList = ({orders}) => {

    return (

        <main>

            <h1 className='header'>Заказы</h1>

            <table className='table-tag'>

                <th className='cell'>ID</th>

                <th className='cell'>Номер заказа</th>

                <th className='cell'>Стоимость, $</th>

                <th className='cell'>Дата доставки</th>

                <th className='cell'>Стоимость, ₽</th>

                {orders.map((order) => <OrderItem order={order}/>)}

            </table>

        </main>
    )

}

export default OrderList;