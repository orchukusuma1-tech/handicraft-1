import os
'currency': currency.lower(),
'quantity': it.qty
})


st.write('Items:')
for li in line_items:
st.write(f"{li['name']} x {li['quantity']} -> {li['amount']/100:.2f} {currency}")
st.write('Total:', total_cents/100.0, currency)


if st.button(strings['place_order']):
# create Stripe Checkout session
if not STRIPE_SECRET_KEY:
st.error('Stripe secret key not configured in env (STRIPE_SECRET_KEY)')
else:
try:
stripe_line_items = []
for li in line_items:
price_data = {
'currency': li['currency'],
'product_data': {'name': li['name']},
'unit_amount': li['amount']
}
stripe_line_items.append({'price_data': price_data, 'quantity': li['quantity']})


session = stripe.checkout.Session.create(
payment_method_types=['card'],
line_items=stripe_line_items,
mode='payment',
success_url=f"{APP_URL}?checkout=success",
cancel_url=f"{APP_URL}?checkout=cancel"
)
# save provisional order
order = Order(user_id=st.session_state['user_id'], items=[{'name':x['name'],'qty':x['quantity'],'amount':x['amount']} for x in line_items], total_cents=total_cents, currency=currency, address={'raw': addr_options.get(sel_id) if sel_addr else None})
db.add(order); db.commit()
st.info('Redirecting to Stripe Checkout...')
st.markdown(f"[Proceed to payment]({session.url})")
except Exception as e:
st.error(f"Stripe error: {e}")


# Chat assistant (bottom)
st.write('---')
st.header(strings['chat_with_ai'])
if 'chat_history' not in st.session_state:
st.session_state['chat_history'] = []


user_input = st.text_input('Ask about products, shipping, or the app', key='chat_input')
if st.button('Send to assistant'):
if not user_input:
st.info('Type a message')
else:
st.session_state['chat_history'].append({'role':'user','content':user_input})
if not OPENAI_API_KEY:
# fallback simple assistant
st.session_state['chat_history'].append({'role':'assistant','content':"(OpenAI API key not set) I can help describe product features, shipping and how to use the app. Ask me anything."})
else:
try:
import openai
openai.api_key = OPENAI_API_KEY
messages = [{'role':m['role'],'content':m['content']} for m in st.session_state['chat_history']]
# include system prompt
system = {'role':'system','content':'You are a friendly e-commerce assistant. Answer briefly and in the user locale.'}
resp = openai.ChatCompletion.create(model='gpt-4o-mini' if hasattr(openai,'ChatCompletion') else 'gpt-4o-mini', messages=[system]+messages, temperature=0.7)
content = resp.choices[0].message.content if resp.choices else 'Sorry, no response.'
st.session_state['chat_history'].append({'role':'assistant','content':content})
except Exception as e:
st.error(f"OpenAI error: {e}")


for m in st.session_state['chat_history'][-10:]:
if m['role']=='user':
st.markdown(f"**You:** {m['content']}")
else:
st.markdown(f"**Assistant:** {m['content']}")


# Footer: quick links
st.write('\n---\n')
st.caption('Starter tribal marketplace — customize further for vendor onboarding, KYC, shipping integrations, and localization.')
